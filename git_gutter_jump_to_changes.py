try:
    from .git_gutter_settings import settings
except ValueError:
    from git_gutter_settings import settings


class GitGutterJumpToChanges(object):
    def __init__(self, git_handler):
        self.git_handler = git_handler

    def goto_line(self, jump_func, all_changes):
        if all_changes:
            view = self.git_handler.view
            row, col = view.rowcol(view.sel()[0].begin())
            current_row = row + 1
            line = jump_func(all_changes, current_row)
            view.run_command("goto_line", {"line": line})

    def jump_to_next_change(self):
        self.goto_line(self.next_jump, self.git_handler.diff_changed_blocks())

    def jump_to_prev_change(self):
        self.goto_line(self.prev_jump, self.git_handler.diff_changed_blocks())

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
