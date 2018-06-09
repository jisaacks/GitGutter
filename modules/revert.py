# -*- coding: utf-8 -*-
from .utils import line_from_kwargs


def revert_change(git_gutter, **kwargs):
    """Revert changed hunk under the cursor.

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
    revert_change_impl(
        git_gutter.view,
        git_gutter.git_handler.diff_line_change(line + 1))


def revert_change_impl(view, diff_info):
    """Revert changes defined by diff_info.

    Arguments:
        view (sublime.View):
            The view in which the changes are to revert.
        diff_info (tuple):
            All the information required to revert the changes.
    """
    del_lines, start, size, meta = diff_info
    if start == -1:
        return

    # extract the type of the hunk: removed, modified, (x)or added
    is_removed = size == 0
    is_modified = not is_removed and bool(del_lines)

    new_text = '\n'.join(del_lines)
    # (removed) if there is no text to remove, set the
    # region to the end of the line, where the hunk starts
    # and add a new line to the start of the text
    if is_removed:
        if start != 0:
            # set the start and the end to the end of the start line
            start_point = end_point = view.text_point(start, 0) - 1
            # add a leading newline before inserting the text
            new_text = '\n' + new_text
        else:
            # (special handling for deleted at the start of the file)
            # if we are before the start we need to set the start
            # to 0 and add the newline behind the text
            start_point = end_point = 0
            new_text = new_text + '\n'
    # (modified/added)
    # set the start point to the start of the hunk
    # and the end point to the end of the hunk
    else:
        start_point = view.text_point(start - 1, 0)
        end_point = view.text_point(start + size - 1, 0)
        # (modified) if there is text to insert, we
        # don't want to capture the trailing newline,
        # because we insert lines without a trailing newline
        if is_modified and end_point != view.size():
            end_point -= 1
    view.run_command('git_gutter_replace_text', {
        'start': start_point, 'end': end_point, 'text': new_text})
