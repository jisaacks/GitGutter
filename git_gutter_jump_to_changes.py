import sublime_plugin

try:
    from .git_gutter_settings import settings
except (ImportError, ValueError):
    from git_gutter_settings import settings


class GitGutterJumpToChanges(object):
    def __init__(self, view, git_handler):
        self.view = view
        self.git_handler = git_handler

    def lines_to_blocks(self, lines):
        blocks = []
        last_line = -2
        for line in lines:
            if line > last_line + 1:
                blocks.append(line)
            last_line = line
        return blocks

    def goto_line(self, jump_func, diff_results):
        inserted, modified, deleted = diff_results
        inserted = self.lines_to_blocks(inserted)
        modified = self.lines_to_blocks(modified)
        all_changes = sorted(inserted + modified + deleted)
        if all_changes:
            row, col = self.view.rowcol(self.view.sel()[0].begin())
            current_row = row + 1
            line = jump_func(all_changes, current_row)
            self.view.run_command("goto_line", {"line": line})

    def jump_to_next_change(self):
        all_changes = self.git_handler.diff()
        self.goto_line(self.next_jump, all_changes)

    def jump_to_prev_change(self):
        all_changes = self.git_handler.diff()
        self.goto_line(self.prev_jump, all_changes)

    def next_jump(self, all_changes, current_row):
        if settings.get('next_prev_change_wrap', True):
            default = all_changes[0]
        else:
            default = all_changes[-1]

        return next((change for change in all_changes
                    if change > current_row), default)

    def prev_jump(self, all_changes, current_row):
        if settings.get('next_prev_change_wrap', True):
            default = all_changes[-1]
        else:
            default = all_changes[0]

        return next((change for change in reversed(all_changes)
                    if change < current_row), default)


# Proxy command provided for backwards compatibility.
class GitGutterNextChangeCommand(sublime_plugin.WindowCommand):
    def run(self):
        print(
            '"git_gutter_next_change" command is deprecated. '
            'Please update your keybindings to use this instead: '
            '"git_gutter", "args": {"action": "jump_to_next_change"}"')
        view = self.window.active_view()
        if view:
            view.run_command('git_gutter', {'action': 'jump_to_next_change'})


# Proxy command provided for backwards compatibility.
class GitGutterPrevChangeCommand(sublime_plugin.WindowCommand):
    def run(self):
        print(
            '"git_gutter_prev_change" command is deprecated. '
            'Please update your keybindings to use this instead: '
            '"git_gutter", "args": {"action": "jump_to_prev_change"}"')
        view = self.window.active_view()
        if view:
            view.run_command('git_gutter', {'action': 'jump_to_prev_change'})
