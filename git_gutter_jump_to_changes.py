from functools import partial

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
        self.git_handler.diff().then(partial(self.goto_line, self.next_jump))

    def jump_to_prev_change(self):
        self.git_handler.diff().then(partial(self.goto_line, self.prev_jump))

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
