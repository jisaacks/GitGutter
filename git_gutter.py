import sublime
import sublime_plugin
try:
    from GitGutter.view_collection import ViewCollection
except ImportError:
    from view_collection import ViewCollection


def plugin_loaded():
    """
    Ugly hack for icons in ST3
    kudos:
    github.com/facelessuser/BracketHighlighter/blob/BH2ST3/bh_core.py#L1380
    """
    from os import makedirs
    from os.path import exists, join

    icon_path = join(sublime.packages_path(), "Theme - Default")
    if not exists(icon_path):
        makedirs(icon_path)


class GitGutterCommand(sublime_plugin.WindowCommand):
    region_names = ['deleted_top', 'deleted_bottom',
                    'deleted_dual', 'inserted', 'changed',
                    'untracked', 'ignored']

    qualifiers = ['staged','unstaged']

    def run(self):
        self.view = self.window.active_view()
        if not self.view:
            # View is not ready yet, try again later.
            sublime.set_timeout(self.run, 1)
            return
        self.clear_all()
        if ViewCollection.untracked(self.view):
            self.bind_files('untracked')
        elif ViewCollection.ignored(self.view):
            self.bind_files('ignored')
        else:
            dirty  = self.view.is_dirty()
            staged = ViewCollection.has_stages(self.view)
            if staged and not dirty:
                # FIXME
                # * dry up the 3 blocks of code below that all look the same
                # * only qualify unstaged changes when there _are_ staged ones

                # Mark changes qualified with staged/unstaged
                inserted, modified, deleted = self.unstaged_changes()
                self.lines_removed(deleted, 'unstaged')
                self.bind_icons('inserted', inserted, 'unstaged')
                self.bind_icons('changed', modified, 'unstaged')
                
                inserted, modified, deleted = self.staged_changes()
                self.lines_removed(deleted, 'staged')
                self.bind_icons('inserted', inserted, 'staged')
                self.bind_icons('changed', modified, 'staged')
            else:
                # Mark changes without a qualifier
                inserted, modified, deleted = self.all_changes()
                self.lines_removed(deleted)
                self.bind_icons('inserted', inserted)
                self.bind_icons('changed', modified)


    def all_changes(self):
        return ViewCollection.diff(self.view)

    def unstaged_changes(self):
        return ViewCollection.staged(self.view)

    def staged_changes(self):
        all_inserted, all_modified, all_deleted = self.all_changes()
        uns_inserted, uns_modified, uns_deleted = self.unstaged_changes()
        
        stg_inserted = self.list_subtract(all_inserted, uns_inserted)
        stg_modified = self.list_subtract(all_modified, uns_modified)
        stg_deleted  = self.list_subtract(all_deleted, uns_deleted)

        return [stg_inserted, stg_modified, stg_deleted]

    def list_subtract(self, a, b):
        subtracted = [elem for elem in a if elem not in b]
        return subtracted

    def clear_all(self):
        for region_name in self.region_names:
            self.view.erase_regions('git_gutter_%s' % region_name)
            for qualifier in self.qualifiers:
                self.view.erase_regions('git_gutter_%s_%s' % (
                    region_name, qualifier))

    def lines_to_regions(self, lines):
        regions = []
        for line in lines:
            position = self.view.text_point(line - 1, 0)
            region = sublime.Region(position, position)
            regions.append(region)
        return regions

    def lines_removed(self, lines, qualifier=None):
        top_lines = lines
        bottom_lines = [line - 1 for line in lines if line > 1]
        dual_lines = []
        for line in top_lines:
            if line in bottom_lines:
                dual_lines.append(line)
        for line in dual_lines:
            bottom_lines.remove(line)
            top_lines.remove(line)

        self.bind_icons('deleted_top', top_lines, qualifier)
        self.bind_icons('deleted_bottom', bottom_lines, qualifier)
        self.bind_icons('deleted_dual', dual_lines, qualifier)

    def icon_path(self, icon_name):
        if int(sublime.version()) < 3014:
            path = '..'
            extn = ''
        else:
            path = 'Packages'
            extn = '.png'
        return path + '/GitGutter/icons/' + icon_name + extn

    def icon_scope(self, event_scope, qualifier):
        scope = 'markup.%s.git_gutter' % event_scope
        if qualifier:
            scope += "." + qualifier
        return scope

    def icon_region(self, event, qualifier):
        region = 'git_gutter_%s' % event
        if qualifier:
            region += "_" + qualifier
        return region

    def bind_icons(self, event, lines, qualifier=None):
        regions = self.lines_to_regions(lines)
        event_scope = event
        if event.startswith('deleted'):
            event_scope = 'deleted'
        scope = self.icon_scope(event_scope,qualifier)
        icon = self.icon_path(event)
        key = self.icon_region(event,qualifier)
        self.view.add_regions(key, regions, scope, icon)

    def bind_files(self, event):
        lines = []
        lineCount = ViewCollection.total_lines(self.view)
        i = 0
        while i < lineCount:
            lines += [i + 1]
            i = i + 1
        self.bind_icons(event, lines)
