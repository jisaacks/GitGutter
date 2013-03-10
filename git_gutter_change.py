import sublime
import sublime_plugin
try:
    from GitGutter.view_collection import ViewCollection
except ImportError:
    from view_collection import ViewCollection

class GitGutterBaseChangeCommand(sublime_plugin.WindowCommand):
    def lines_to_blocks(self, lines):
        blocks = []
        last_line = -2
        for line in lines:
            if line > last_line+1:
                blocks.append(line)
            last_line = line
        return blocks

    def run(self):
        view = self.window.active_view()

        inserted, modified, deleted = ViewCollection.diff(view)
        inserted = self.lines_to_blocks(inserted)
        modified = self.lines_to_blocks(modified)
        all_changes = sorted(inserted + modified + deleted)

        row, col = view.rowcol(view.sel()[0].begin())

        current_row = row + 1
        
        line = self.jump(all_changes, current_row)

        self.window.active_view().run_command("goto_line", {"line": line})

class GitGutterNextChangeCommand(GitGutterBaseChangeCommand):
    def jump(self, all_changes, current_row):
        return next((change for change in all_changes
                        if change > current_row), all_changes[0])


class GitGutterPrevChangeCommand(GitGutterBaseChangeCommand):
    def jump(self, all_changes, current_row):
        return next((change for change in reversed(all_changes)
                        if change < current_row), all_changes[-1])