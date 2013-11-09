import os
import sublime
import sublime_plugin

try:
    from .view_collection import ViewCollection
except (ImportError, ValueError):
    from view_collection import ViewCollection

ST3 = int(sublime.version()) >= 3000


def plugin_loaded():
    global settings
    settings = sublime.load_settings('GitGutter.sublime-settings')


class GitGutterCommand(sublime_plugin.WindowCommand):
    region_names = ['deleted_top', 'deleted_bottom',
                    'deleted_dual', 'inserted', 'changed',
                    'untracked', 'ignored']

    def run(self, force_refresh=False):
        self.view = self.window.active_view()
        if not self.view:
            # View is not ready yet, try again later.
            sublime.set_timeout(self.run, 1)
            return

        self.clear_all()
        show_untracked = settings.get('show_markers_on_untracked_file', False)

        if ViewCollection.untracked(self.view):
            if show_untracked:
                self.bind_files('untracked')
        elif ViewCollection.ignored(self.view):
            if show_untracked:
                self.bind_files('ignored')
        else:
            # If the file is untracked there is no need to execute the diff
            # update
            if force_refresh:
                ViewCollection.clear_git_time(self.view)
            inserted, modified, deleted = ViewCollection.diff(self.view)
            self.lines_removed(deleted)
            self.bind_icons('inserted', inserted)
            self.bind_icons('changed', modified)

            if(ViewCollection.show_status(self.view) != "none"):
                if(ViewCollection.show_status(self.view) == 'all'):
                    branch = ViewCollection.current_branch(
                        self.view).decode("utf-8").strip()
                else:
                    branch = ""

                self.update_status(len(inserted),
                                   len(modified),
                                   len(deleted),
                                   ViewCollection.get_compare(self.view), branch)
            else:
                self.update_status(0, 0, 0, "", "")

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

    def is_region_protected(self, region):
        # Load protected Regions from Settings
        protected_regions = settings.get('protected_regions',[])
        # List of Lists of Regions
        sets = [self.view.get_regions(r) for r in protected_regions]
        # List of Regions
        regions = [r for rs in sets for r in rs]
        for r in regions:
            if r.contains(region):
                return True

        return False

    def lines_to_regions(self, lines):
        regions = []
        for line in lines:
            position = self.view.text_point(line - 1, 0)
            region = sublime.Region(position, position)
            if not self.is_region_protected(region):
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
        lineCount = ViewCollection.total_lines(self.view)
        i = 0
        while i < lineCount:
            lines += [i + 1]
            i = i + 1
        self.bind_icons(event, lines)


if not ST3:
    plugin_loaded()
