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

    def run(self):
        self.view = self.window.active_view()
        if not self.view:
            # View is not ready yet, try again later.
            sublime.set_timeout(self.run, 1)
            return
        self.clear_all()
        inserted, modified, deleted = ViewCollection.diff(self.view)
        self.lines_removed(deleted)
        self.lines_added(inserted)
        self.lines_modified(modified)

    def clear_all(self):
        self.view.erase_regions('git_gutter_deleted_top')
        self.view.erase_regions('git_gutter_deleted_bottom')
        self.view.erase_regions('git_gutter_deleted_dual')
        self.view.erase_regions('git_gutter_inserted')
        self.view.erase_regions('git_gutter_changed')

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

        self.lines_removed_top(top_lines)
        self.lines_removed_bottom(bottom_lines)
        self.lines_removed_dual(dual_lines)

    def icon_path(self, icon_name):
        if int(sublime.version()) < 3014:
            path = '..'
            extn = ''
        else:
            path = 'Packages'
            extn = '.png'
        return path + '/GitGutter/icons/' + icon_name + extn

    def lines_removed_top(self, lines):
        regions = self.lines_to_regions(lines)
        scope = 'markup.deleted.git_gutter'
        icon = self.icon_path('deleted_top')
        self.view.add_regions('git_gutter_deleted_top', regions, scope, icon)

    def lines_removed_bottom(self, lines):
        regions = self.lines_to_regions(lines)
        scope = 'markup.deleted.git_gutter'
        icon = self.icon_path('deleted_bottom')
        self.view.add_regions('git_gutter_deleted_bottom', regions, scope, icon)

    def lines_removed_dual(self, lines):
        regions = self.lines_to_regions(lines)
        scope = 'markup.deleted.git_gutter'
        icon = self.icon_path('deleted_dual')
        self.view.add_regions('git_gutter_deleted_dual', regions, scope, icon)

    def lines_added(self, lines):
        regions = self.lines_to_regions(lines)
        scope = 'markup.inserted.git_gutter'
        icon = self.icon_path('inserted')
        self.view.add_regions('git_gutter_inserted', regions, scope, icon)

    def lines_modified(self, lines):
        regions = self.lines_to_regions(lines)
        scope = 'markup.changed.git_gutter'
        icon = self.icon_path('changed')
        self.view.add_regions('git_gutter_changed', regions, scope, icon)
