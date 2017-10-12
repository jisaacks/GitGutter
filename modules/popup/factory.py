# -*- coding: utf-8 -*-
"""Diff Popup Factory Module.

Contains all functions required to built the diff popup and its content.
"""
import sublime
import mdpopups
from . import differ
from .. import revert


def show_diff_popup(git_gutter, **kwargs):
    """Show the diff popup.

    Arguments:
        git_gutter (GitGutterCommand):
            The main command object, which represents GitGutter.
        kwargs (dict):
            The arguments passed from GitGutterDiffPopupCommand
            to GitGutterCommand.
    """
    if not git_gutter.git_handler.in_repo():
        return
    # validate highlighting argument
    highlight_diff = kwargs.get('highlight_diff')
    if highlight_diff is None:
        mode = git_gutter.settings.get('diff_popup_default_mode', '')
        highlight_diff = mode == 'diff'
    # validate point argument
    point = kwargs.get('point')
    if point is None:
        selection = git_gutter.view.sel()
        if not selection:
            return
        point = selection[0].end()
    # get line number from text point
    line = git_gutter.view.rowcol(point)[0] + 1
    # create popup asynchronously in case it takes several 100ms
    _show_diff_popup_impl(
        git_gutter, line, highlight_diff, kwargs.get('flags', 0),
        git_gutter.git_handler.diff_line_change(line))


def _show_diff_popup_impl(git_gutter, line, highlight_diff, flags, diff_info):
    """Show and update the diff popup.

    Arguments:
        git_gutter (GitGutterCommand):
            The main command object, which represents GitGutter.
        line (int):
            The line number the diff popup is requested for
        highlight_diff (bool):
            If True to the diff is displayed instead of the old revision.
        flags (int):
            Sublime Text popup flags.
        diff_info (tuple):
            All the information required to display the diff popup.
    """
    del_lines, start, size, meta = diff_info
    if start == -1:
        return

    view = git_gutter.view

    # extract the type of the hunk: removed, modified, (x)or added
    is_removed = size == 0
    is_modified = not is_removed and bool(del_lines)
    is_added = not is_removed and not is_modified

    def navigate(href):
        # allow navigate() to manipulate the outer variables
        nonlocal highlight_diff

        if href == 'hide':
            view.hide_popup()
        elif href == 'copy':
            del_text = '\n'.join(del_lines)
            sublime.set_clipboard(del_text)
            sublime.status_message(
                'Copied: {0} characters'.format(len(del_text)))
        elif href == 'revert':
            # hide the popup and update the view
            view.hide_popup()
            revert.revert_change_impl(view, diff_info)
        elif href == 'disable_hl_diff':
            # show a diff popup with the same diff info (previous revision)
            highlight_diff = False
            _show_diff_popup_impl(
                git_gutter, line, highlight_diff, flags, diff_info)
        elif href == 'enable_hl_diff':
            # show a diff popup with the same diff info (highlight diff)
            highlight_diff = True
            _show_diff_popup_impl(
                git_gutter, line, highlight_diff, flags, diff_info)
        elif href in ('first_change', 'next_change', 'prev_change'):
            next_line = meta.get(href, line)
            point = view.text_point(next_line - 1, 0)

            def show_new_popup():
                # wait until scrolling has completed
                if not view.visible_region().contains(point):
                    return sublime.set_timeout_async(show_new_popup, 20)
                # show a diff popup with new diff info
                _show_diff_popup_impl(
                    git_gutter, next_line, highlight_diff, 0,
                    git_gutter.git_handler.diff_line_change(next_line))
            view.hide_popup()
            view.show_at_center(point)
            show_new_popup()

    # write the symbols/text for each button
    buttons = _built_toolbar_buttons(start, meta)
    location = _visible_text_point(view, line - 1, 0)
    code_wrap = view.settings().get('word_wrap')
    if code_wrap == 'auto':
        code_wrap = view.match_selector(location, 'source')

    if highlight_diff:
        # (*) show a highlighted diff of the merged git and editor content
        new_lines = meta['added_lines']
        tab_width = view.settings().get('tab_width', 4)
        min_indent = _get_min_indent(del_lines + new_lines, tab_width)
        content = (
            '<div class="toolbar">'
            '{hide} '
            '{first_change} {prev_change} {next_change} '
            '{disable_hl_diff} {revert}'
            '</div>'
            .format(**buttons)
        ) + differ.highlight_diff(
            [line.expandtabs(tab_width)[min_indent:] for line in del_lines],
            [line.expandtabs(tab_width)[min_indent:] for line in new_lines])

    elif not is_added:
        # (modified/removed) show content from git database
        tab_width = view.settings().get('tab_width', 4)
        min_indent = _get_min_indent(del_lines, tab_width)
        source_content = '\n'.join(
            (line.expandtabs(tab_width)[min_indent:] for line in del_lines))
        # common arguments used to highlight the content
        popup_kwargs = {
            'allow_code_wrap': code_wrap,
            'language': mdpopups.get_language_from_view(view) or ''
        }
        content = (
            '<div class="toolbar">'
            '{hide} '
            '{first_change} {prev_change} {next_change} '
            '{enable_hl_diff} {copy} {revert}'
            '</div>'
            .format(**buttons)
        ) + mdpopups.syntax_highlight(view, source_content, **popup_kwargs)

    else:
        # (added) only show the button line without the copy button
        # (there is nothing to show or copy)
        content = (
            '<div class="toolbar">'
            '{hide} '
            '{first_change} {prev_change} {next_change} '
            '{enable_hl_diff} {revert}'
            '</div>'
            .format(**buttons)
        )

    # common arguments used to create or update the popup
    popup_kwargs = {
        'view': view,
        'content': content,
        'md': False,
        'css': _load_popup_css(git_gutter.settings.theme_path),
        'wrapper_class': 'git-gutter',
        'allow_code_wrap': code_wrap
    }
    # update visible popup
    if view.is_popup_visible():
        return mdpopups.update_popup(**popup_kwargs)
    # calculate optimal popup width to apply desired wrapping
    popup_width = int(view.viewport_extent()[0])
    if code_wrap:
        line_length = view.settings().get('wrap_width', 0)
        if line_length > 0:
            popup_width = (line_length + 5) * view.em_width()
    # create new popup
    return mdpopups.show_popup(
        location=location, max_width=popup_width, flags=flags,
        on_navigate=navigate, **popup_kwargs)


def _built_toolbar_buttons(start, meta):
    """Built the toolbar buttons with icon/text as link/label.

    Each toolbar button needs to be rendered using the unicode icon character
    or a text label for those who don't like icons. If enabled each button is
    attached to a <a> link.

    Arguments:
        start (int):
            First line of the current hunk.
        meta (dict):
            The dictionay containing additional hunk information.

    Returns:
        dict: The dictionay with all buttons where `key` is used as `href`
            and value as link caption.

            active icon button: <a href="revert"><symbol>⟲</symbol></a>
            active text button: <a href="revert"><text>(revert)</text></a>
            inactive icon button: <symbol>⟲</symbol>
            inactive text button: <text>(revert)</text>
    """
    # The format to render disabled/enabled buttons
    button_format = (
        '<symbol>{0}</symbol>',
        '<a href="{1}"><symbol>{0}</symbol></a>'
    )
    # The buttons as a map from the href to the caption/icon
    button_caption = {
        'hide': '×',
        'copy': '⎘',
        'revert': '⟲',
        'disable_hl_diff': '≉',
        'enable_hl_diff': '≈',
        'first_change':  '⤒',
        'prev_change': '↑',
        'next_change': '↓'
    }
    return {
        key: button_format[
            not key.endswith('_change') or meta.get(key, start) != start
        ].format(value, key) for key, value in button_caption.items()
    }


def _load_popup_css(theme_path):
    """Load and join popup stylesheets.

    Arguments:
        theme_path (string):
            The path to the active gitgutter-theme file.
    """
    css_lines = []
    for path in ('Packages/GitGutter', theme_path, 'Packages/User'):
        try:
            css_path = path + '/gitgutter_popup.css'
            css_lines.append(sublime.load_resource(css_path))
        except IOError:
            pass
    return ''.join(css_lines)


def _get_min_indent(lines, tab_width=4):
    """Find the minimum count of indenting whitespaces in lines.

    Arguments:
        lines (tuple):
            The content to search the minimum indention for.
        tab_width (int):
            The number of spaces expand tabs before searching for indention by.
    """
    min_indent = 2**32
    for line in lines:
        i = 0
        for c in line:
            if c == ' ':
                i += 1
            elif c == '\t':
                i += tab_width - (i % tab_width)
            else:
                break

        if min_indent > i:
            min_indent = i
        if not min_indent:
            break
    return min_indent


def _visible_text_point(view, row, col):
    """Return the text_point of row,col clipped to the visible viewport.

    Arguments:
        view (sublime.View):
            the view to return the text_point for
        row (int):
            the row to use for text_point calculation
        col (int):
            the column relative to the first visible column of the viewport
            which is defined by the horizontal scroll position.
    Returns:
        int: The text_point of row & col within the viewport.
    """
    viewport = view.visible_region()
    _, vp_col = view.rowcol(viewport.begin())
    return view.text_point(row, vp_col + col)
