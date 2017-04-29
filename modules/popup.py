# -*- coding: utf-8 -*-
import sublime
import sublime_plugin

try:
    if int(sublime.version()) < 3080:
        raise ImportError('No popup available.')

    import difflib
    import html
    import jinja2
    import mdpopups

    _MDPOPUPS_INSTALLED = True
except ImportError:
    _MDPOPUPS_INSTALLED = False

_MD_POPUPS_USE_WRAPPER_CLASS = int(sublime.version()) >= 3119


def show_diff_popup(git_gutter, **kwargs):
    """Show the diff popup.

    Arguments:
        git_gutter (GitGutterCommand):
            The main command object, which represents GitGutter.
        kwargs (dict):
            The arguments passed from GitGutterDiffPopupCommand
            to GitGutterCommand.
    """
    if not _MDPOPUPS_INSTALLED or not git_gutter.git_handler.in_repo():
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
    sublime.set_timeout_async(
        lambda: _show_diff_popup_impl(
            git_gutter, line, highlight_diff, kwargs.get('flags', 0),
            git_gutter.git_handler.diff_line_change(line)))


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
    deleted_lines, start, size, meta = diff_info
    if start == -1:
        return

    view = git_gutter.view

    # extract the type of the hunk: removed, modified, (x)or added
    is_removed = size == 0
    is_modified = not is_removed and bool(deleted_lines)
    is_added = not is_removed and not is_modified

    def navigate(href):
        if href == 'hide':
            view.hide_popup()
        elif href == 'copy':
            sublime.set_clipboard(deleted_lines)
            sublime.status_message(
                'Copied: {0} characters'.format(len(deleted_lines)))
        elif href == 'revert':
            new_text = '\n'.join(deleted_lines)
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
            # hide the popup and update the view
            view.hide_popup()
            view.run_command('git_gutter_replace_text', {
                'start': start_point, 'end': end_point, 'text': new_text})
        elif href == 'disable_hl_diff':
            # show a diff popup with the same diff info (previous revision)
            _show_diff_popup_impl(git_gutter, line, False, flags, diff_info)
        elif href == 'enable_hl_diff':
            # show a diff popup with the same diff info (highlight diff)
            _show_diff_popup_impl(git_gutter, line, True, flags, diff_info)
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
            view.show_at_center(point)
            show_new_popup()

    # write the symbols/text for each button
    use_icons = git_gutter.settings.get('diff_popup_use_icon_buttons')
    # the buttons as a map from the href to the caption/icon
    button_descriptions = {
        'hide': '×' if use_icons else '(close)',
        'copy': '⎘' if use_icons else '(copy)',
        'revert': '⟲' if use_icons else '(revert)',
        'disable_hl_diff': '≉' if use_icons else '(diff)',
        'enable_hl_diff': '≈' if use_icons else '(diff)',
        'first_change': '⤒' if use_icons else '(first)',
        'prev_change': '↑' if use_icons else '(previous)',
        'next_change': '↓' if use_icons else '(next)'
    }
    button_fmt = '<span class="gitgutter-button"><a href="{1}">{0}</a></span>'
    button_disabled_fmt = '<span class="gitgutter-button">{0}</span>'
    buttons = {}
    for key, value in button_descriptions.items():
        if not key.endswith('_change') or meta.get(key, start) != start:
            buttons[key] = button_fmt.format(value, key)
        else:
            buttons[key] = button_disabled_fmt.format(value)

    if highlight_diff:
        # (*) show a highlighted diff of the merged git and editor content
        new_lines = meta['added_lines']
        tab_width = view.settings().get('tab_width', 4)
        min_indent = _get_min_indent(deleted_lines + new_lines, tab_width)
        content = (
            '{hide} '
            '{first_change} {prev_change} {next_change} '
            '{disable_hl_diff} {revert}'
            .format(**buttons)
        ) + _highlight_diff(
            '\n'.join(line[min_indent:] for line in deleted_lines),
            '\n'.join(line[min_indent:] for line in new_lines))

    elif not is_added:
        # (modified/removed) show content from git database
        lang = mdpopups.get_language_from_view(view) or ''
        tab_width = view.settings().get('tab_width', 4)
        min_indent = _get_min_indent(deleted_lines, tab_width)
        source_content = '\n'.join(line[min_indent:] for line in deleted_lines)
        # replace spaces by non-breakable ones to avoid line wrapping
        # (this has been added to mdpopups in version 1.11.0)
        if mdpopups.version() < (1, 11, 0):
            source_content = source_content.replace(' ', '\u00A0')
        content = (
            '{hide} '
            '{first_change} {prev_change} {next_change} '
            '{enable_hl_diff} {copy} {revert}'
            .format(**buttons)
        ) + mdpopups.syntax_highlight(
            view, source_content, language=lang)

    else:
        # (added) only show the button line without the copy button
        # (there is nothing to show or copy)
        content = (
            '{hide} '
            '{first_change} {prev_change} {next_change} '
            '{enable_hl_diff} {revert}'
            .format(**buttons)
        )

    wrapper_class = '.git-gutter' if _MD_POPUPS_USE_WRAPPER_CLASS else ''

    # load and join popup stylesheets
    css_lines = []
    theme_paths = (
        'Packages/GitGutter',
        git_gutter.settings.theme_path,
        'Packages/User'
    )
    for path in theme_paths:
        try:
            resource_name = path + '/gitgutter_popup.css'
            css_lines.append(sublime.load_resource(resource_name))
        except IOError:
            pass

    # apply the jinja template
    jinja_kwargs = {
        'st_version': sublime.version(),
        'wrapper_class': wrapper_class,
        'use_icons': use_icons
    }
    tmpl = jinja2.environment.Template('\n'.join(css_lines))
    css = tmpl.render(**jinja_kwargs)
    # if the ST version does not support the wrapper class, remove it
    if not _MD_POPUPS_USE_WRAPPER_CLASS:
        css = css.replace(wrapper_class, '')

    # create the popup
    location = view.text_point(line - 1, 0)
    window_width = int(view.viewport_extent()[0])
    mdpopups.show_popup(
        view, content, location=location, on_navigate=navigate, md=False,
        wrapper_class=wrapper_class[1:], css=css,
        flags=flags, max_width=window_width)


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
        if not line:
            continue
        line = line.expandtabs(tab_width)
        i, n = 0, len(line)
        while i < n and line[i] == ' ':
            i += 1
        if min_indent > i:
            min_indent = i
        if not min_indent:
            break
    return min_indent


def _highlight_diff(old_content, new_content):
    """Diff two strings and convert to HTML to be displayed in the popup.

    Arguments:
        old_content (string):
            The content from the last git `archive` call.
        new_content (string):
            The content from the view.

    Returns:
        string: The diff result encoded as HTML.
    """
    seq_matcher = difflib.SequenceMatcher(None, old_content, new_content)

    tag_eq = '<span class="gitgutter-hi-equal">'
    tag_ins = '<span class="gitgutter-hi-inserted">'
    tag_del = '<span class="gitgutter-hi-deleted">'
    tag_modified_ins = (
        '<span class="gitgutter-hi-changed gitgutter-hi-inserted">'
    )
    tag_modified_del = (
        '<span class="gitgutter-hi-changed gitgutter-hi-deleted">'
    )
    tag_close = '</span>'

    # build the html string
    lines = ['<div class="highlight">', '<pre>']
    for opcodes in seq_matcher.get_opcodes():
        op_type, git_start, git_end, edit_start, edit_end = opcodes
        if op_type == 'equal':
            lines.append(tag_eq)
            lines.append(_to_html(old_content[git_start:git_end]))
            lines.append(tag_close)
        elif op_type == 'delete':
            lines.append(tag_del)
            lines.append(_to_html(old_content[git_start:git_end]))
            lines.append(tag_close)
        elif op_type == 'insert':
            lines.append(tag_ins)
            lines.append(_to_html(new_content[edit_start:edit_end]))
            lines.append(tag_close)
        elif op_type == 'replace':
            lines.append(tag_modified_ins)
            lines.append(_to_html(new_content[edit_start:edit_end]))
            lines.append(tag_close)
            lines.append(tag_modified_del)
            lines.append(_to_html(old_content[git_start:git_end]))
            lines.append(tag_close)
    lines.extend(['</pre>', '</div>'])
    return ''.join(lines)


def _to_html(text):
    return (
        html.escape(text, quote=False)
        .replace('\n', '<br>')
        .replace(' ', '&nbsp;')
        .replace('\u00A0', '&nbsp;')
    )


class GitGutterReplaceTextCommand(sublime_plugin.TextCommand):
    """The git_gutter_replace_text command implementation."""

    def run(self, edit, start, end, text):
        """Replace the content of a region with new text.

        Arguments:
            edit (Edit):
                The edit object to identify this operation.
            start (int):
                The beginning of the Region to replace.
            end (int):
                The end of the Region to replace.
            text (string):
                The new text to replace the content of the Region with.
        """
        region = sublime.Region(start, end)
        self.view.replace(edit, region, text)


class GitGutterDiffPopupCommand(sublime_plugin.TextCommand):
    """The git_gutter_diff_popup command implemention."""

    def is_enabled(self):
        """Check whether diff popup is enabled for the view."""
        return (
            _MDPOPUPS_INSTALLED and
            self.view.settings().get('git_gutter_is_enabled', False))

    def run(self, edit, point=None, highlight_diff=None, flags=0):
        """Run git_gutter(show_diff_popup, ...) command.

        Arguments:
            edit (Edit):
                The edit object to identify this operation (unused).
            point (int):
                The text position to show the diff popup for.
            highlight_diff (string or bool):
                The desired initial state of dispayed popup content.
                "default": show old state of the selected hunk
                "diff": show diff between current and old state
            flags (int):
                One of Sublime Text's popup flags.
        """
        self.view.run_command('git_gutter', {
            'action': 'show_diff_popup', 'point': point,
            'highlight_diff': highlight_diff, 'flags': flags})
