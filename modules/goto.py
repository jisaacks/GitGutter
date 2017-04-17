# -*- coding: utf-8 -*-


def next_change(git_gutter, **kwargs):
    """Move cursor to the beginning of the next changed hunk.

    Arguments:
        git_gutter (GitGutterCommand): The main command object, which
            represents GitGutter.
        kwargs (dict): The arguments received from the `run_command`.
            This argument is declared to create a common interface being used
            by the GitGutterCommand object.
    """
    _goto_change(git_gutter, _find_next_change)


def prev_change(git_gutter, **kwargs):
    """Move cursor to the beginning of the previous changed hunk.

    Arguments:
        git_gutter (GitGutterCommand): The main command object, which
            represents GitGutter.
        kwargs (dict): The arguments received from the `run_command`.
            This argument is declared to create a common interface being used
            by the GitGutterCommand object.
    """
    _goto_change(git_gutter, _find_prev_change)


def _goto_change(git_gutter, jump_func):
    """Get a tuple of changes and goto the next one found by jump_func.

    Arguments:
        git_gutter (GitGutterCommand): The main command object, which
            represents GitGutter.
        jump_func (function): The function to use to select the next hunk from
            the list of changes.
    """
    selections = git_gutter.view.sel()
    if not selections:
        return
    changes = git_gutter.git_handler.diff_changed_blocks()
    if not changes:
        return
    current_row, _ = git_gutter.view.rowcol(selections[0].begin())
    wrap = git_gutter.settings.get('next_prev_change_wrap', True)
    line = jump_func(changes, current_row + 1, wrap)
    git_gutter.view.run_command("goto_line", {"line": line})


def _find_next_change(changes, current_row, wrap):
    """Find the next line after current row in changes.

    Arguments:
        changes (list): The list of first lines of changed hunks.
        current_row (int): The row to start searching from.
        wrap (bool): If True continue with first change after end of file.

    Returns:
        int: The next line in changes.
    """
    return next(
        (change for change in changes if change > current_row),
        changes[0] if wrap else changes[-1])


def _find_prev_change(changes, current_row, wrap):
    """Find the previous line before current row in changes.

    Arguments:
        changes (list): The list of first lines of changed hunks.
        current_row (int): The row to start searching from.
        wrap (bool): If True continue with first change after end of file.

    Returns:
        int: The previous line in changes.
    """
    return next(
        (change for change in reversed(changes) if change < current_row),
        changes[-1] if wrap else changes[0])
