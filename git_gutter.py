import os
import sublime
import sublime_plugin
try:
    from .git_gutter_handler import GitGutterHandler
    from .git_gutter_settings import GitGutterSettings
    from .git_gutter_jump_to_changes import GitGutterJumpToChanges
    from .promise import Promise, ConstPromise
except (ImportError, ValueError):
    from git_gutter_handler import GitGutterHandler
    from git_gutter_settings import GitGutterSettings
    from git_gutter_jump_to_changes import GitGutterJumpToChanges
    from promise import Promise, ConstPromise

ST3 = int(sublime.version()) >= 3000

class GitGutterCommand(sublime_plugin.TextCommand):
    region_names = ['deleted_top', 'deleted_bottom',
                    'deleted_dual', 'inserted', 'changed',
                    'untracked', 'ignored']

    def __init__(self, *args, **kwargs):
        sublime_plugin.TextCommand.__init__(self, *args, **kwargs)
        self.settings = sublime.load_settings('GitGutter.sublime-settings')
        self.git_handler = GitGutterHandler(self.view)
        self.jump_handler = GitGutterJumpToChanges(self.view, self.git_handler)
        self.diff_results = None

    def run(self, edit_permit, **kwargs):
        if kwargs and 'action' in kwargs:
            action = kwargs['action']
            if action == 'jump_to_next_change':
                self.jump_handler.jump_to_next_change()
            elif action == 'jump_to_prev_change':
                self.jump_handler.jump_to_prev_change()

        elif (self.git_handler.on_disk()):
            self.git_handler.diff().flatMap(self.check_ignored_or_untracked)

    def check_ignored_or_untracked(self, contents):
        if self.show_untracked() and self.are_all_lines_added(contents):
            def bind_ignored_or_untracked(is_ignored):
                if (is_ignored):
                    return ConstPromise(self.bind_files('ignored'))
                else:
                    def bind_untracked(is_untracked):
                        if (is_untracked):
                            self.bind_files('untracked')
                    return self.git_handler.untracked().addCallback(bind_untracked)

            return self.git_handler.ignored().flatMap(bind_ignored_or_untracked)
        else:
            return self.lazy_update_ui(contents)

    # heuristic to determine if the file is either untracked or ignored: all lines show up as "inserted"
    # in the diff. Relying on the output of the normal diff command to trigger the actual untracked /
    # ignored check (which is expensive because it's two separate git ls-files calls) allows us to
    # save the extra git calls
    def are_all_lines_added(self, contents):
        inserted, modified, deleted = contents
        if (len(modified) == 0 and len(deleted) == 0):
            chars = self.view.size()
            region = sublime.Region(0, chars)
            return len(self.view.split_by_newlines(region)) == len(inserted)
        else:
            return False

    def lazy_update_ui(self, contents):
        if (self.diff_results is None or self.diff_results != contents):
            self.diff_results = contents
            return self.update_ui(contents)
        else:
            return ConstPromise(None)

    def update_ui(self, contents):
        inserted, modified, deleted = contents
        self.clear_all()
        self.lines_removed(deleted)
        self.bind_icons('inserted', inserted)
        self.bind_icons('changed', modified)

        if(self.show_status() != "none"):
            if(self.show_status() == 'all'):
                def decode_and_strip(branch_name):
                    return branch_name.decode("utf-8").strip()
                branchPromise = self.git_handler.git_current_branch().map(decode_and_strip)
            else:
                branchPromise = ConstPromise("")

            def update_status_ui(branch_name):
                self.update_status(len(inserted),
                                   len(modified),
                                   len(deleted),
                                   self.compare_against(),
                                   branch_name)
            return branchPromise.addCallback(update_status_ui)
        else:
            return ConstPromise(self.update_status(0, 0, 0, "", ""))

    def update_status(self, inserted, modified, deleted, compare, branch):

        def set_status_if(test, key, message):
            if test:
                self.view.set_status("git_gutter_status_" + key, message)
            else:
                self.view.set_status("git_gutter_status_" + key, "")

        set_status_if(inserted > 0, "inserted", "Inserted : %d" % inserted)
        set_status_if(modified > 0, "modified", "Modified : %d" % modified)
        set_status_if(deleted > 0, "deleted", "Deleted : %d regions" % deleted)
        set_status_if(compare, "comparison", "Comparing against : %s" % compare)
        set_status_if(branch, "branch", "On branch : %s" % branch)

    def clear_all(self):
        for region_name in self.region_names:
            self.view.erase_regions('git_gutter_%s' % region_name)

    def lines_to_regions(self, lines):
        regions = []
        for line in lines:
            position = self.view.text_point(line - 1, 0)
            region = sublime.Region(position, position)
            regions.append(region)
        return regions

    def lines_removed(self, lines):
        top_lines = lines
        bottom_lines = [line - 1 for line in lines if line > 1]
        dual_lines = []
        for line in top_lines:
            if line in bottom_lines:
                dual_lines.append(line)
        for line in dual_lines:
            bottom_lines.remove(line)
            top_lines.remove(line)

        self.bind_icons('deleted_top', top_lines)
        self.bind_icons('deleted_bottom', bottom_lines)
        self.bind_icons('deleted_dual', dual_lines)

    def plugin_dir(self):
        path = os.path.realpath(__file__)
        root = os.path.split(os.path.dirname(path))[1]
        return os.path.splitext(root)[0]

    def icon_path(self, icon_name):
        if icon_name in ['deleted_top','deleted_bottom','deleted_dual']:
            if self.view.line_height() > 15:
                icon_name = icon_name + "_arrow"

        if int(sublime.version()) < 3014:
            path = '../GitGutter'
            extn = ''
        else:
            path = 'Packages/' + self.plugin_dir()
            extn = '.png'

        return "/".join([path, 'icons', icon_name + extn])

    def bind_icons(self, event, lines):
        regions = self.lines_to_regions(lines)
        event_scope = event
        if event.startswith('deleted'):
            event_scope = 'deleted'
        scope = 'markup.%s.git_gutter' % event_scope
        icon = self.icon_path(event)
        self.view.add_regions('git_gutter_%s' % event, regions, scope, icon)

    def bind_files(self, event):
        lines = []
        lineCount = self.total_lines()
        i = 0
        while i < lineCount:
            lines += [i + 1]
            i = i + 1
        self.bind_icons(event, lines)

    def total_lines(self):
        chars = self.view.size()
        region = sublime.Region(0, chars)
        lines = self.view.lines(region)
        return len(lines)

    # Settings

    def show_status(self):
        return GitGutterSettings.get('show_status', 'default')

    def show_untracked(self):
        return GitGutterSettings.get('show_markers_on_untracked_file', False)

    def compare_against(self):
        return GitGutterSettings.get('git_gutter_compare_against', 'HEAD')