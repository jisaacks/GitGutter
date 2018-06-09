# -*- coding: utf-8 -*-
import sublime

from .utils import line_from_kwargs


def copy_from_commit(git_gutter, **kwargs):
    """Copy the content from commit.

    Arguments:
        git_gutter (GitGutterCommand):
            The main command object, which represents GitGutter
            and called this functiond.
        kwargs (dict):
            The arguments passed from GitGutterRevertChangesCommand
            to GitGutterCommand.

            valid kwargs are:
                line (int): zero-based line number within the hunk to copy
                point (int): zero based text position within the hunk to copy
    """
    line = line_from_kwargs(git_gutter.view, kwargs)
    del_lines, _, _, _ = git_gutter.git_handler.diff_line_change(line + 1)
    del_text = '\n'.join(del_lines or '')
    sublime.set_clipboard(del_text)
    sublime.status_message('Copied: {0} characters'.format(len(del_text)))
