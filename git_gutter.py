import sublime
import sublime_plugin
from view_collection import ViewCollection


class GitGutterCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.view = self.window.active_view()
        self.clear_all()
        inserted, modified, deleted = ViewCollection.diff(self.view)
        self.lines_removed(deleted)
        self.lines_added(inserted)
        self.lines_modified(modified)

    def clear_all(self):
        self.view.erase_regions('git_gutter_deleted_top')
        self.view.erase_regions('git_gutter_deleted_bottom')
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
        bottom_lines = []
        for line in lines:
            if line != 1:
                bottom_lines.append(line - 1)
        self.lines_removed_top(lines)
        self.lines_removed_bottom(bottom_lines)

    def lines_removed_top(self, lines):
        regions = self.lines_to_regions(lines)
        scope = 'markup.deleted'
        icon = '../GitGutter/icons/deleted_top'
        self.view.add_regions('git_gutter_deleted_top', regions, scope, icon)

    def lines_removed_bottom(self, lines):
        regions = self.lines_to_regions(lines)
        scope = 'markup.deleted'
        icon = '../GitGutter/icons/deleted_bottom'
        self.view.add_regions('git_gutter_deleted_bottom', regions, scope, icon)

    def lines_added(self, lines):
        regions = self.lines_to_regions(lines)
        scope = 'markup.inserted'
        icon = '../GitGutter/icons/inserted'
        self.view.add_regions('git_gutter_inserted', regions, scope, icon)

    def lines_modified(self, lines):
        regions = self.lines_to_regions(lines)
        scope = 'markup.changed'
        icon = '../GitGutter/icons/changed'
        self.view.add_regions('git_gutter_changed', regions, scope, icon)
