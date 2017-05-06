# -*- coding: utf-8 -*-
import sublime
import sublime_plugin

try:
    # mdpopups needs 3119+ for wrapper_class, which diff popup relies on
    if int(sublime.version()) < 3119:
        raise ImportError('Sublime Text 3119+ required.')

    import difflib
    import html
    import mdpopups

    # mdpopups 1.9.0+ is required because of wrapper_class and templates
    if mdpopups.version() < (1, 9, 0):
        raise ImportError('mdpopups 1.9.0+ required.')
    _MDPOPUPS_INSTALLED = True
    # mdpopups 1.11.0+ can handle none wrapping whitespace
    _MDPOPUPS_HAVE_FIXED_SPACE = mdpopups.version() >= (1, 11, 0)
    # mdpopups 2.0.0+ allows to switch code wrapping on or off
    _MDPOPUPS_HAVE_CODE_WRAP = mdpopups.version() >= (2, 0, 0)
except ImportError:
    _MDPOPUPS_INSTALLED = False


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
        # allow navigate() to manipulate the outer variables
        nonlocal highlight_diff

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
    use_icons = bool(git_gutter.settings.get('diff_popup_use_icon_buttons'))
    buttons = _built_toolbar_buttons(start, meta, use_icons)
    location = view.text_point(line - 1, 0)
    # code wrapping is supported by mdpopups 2.0.0 or higher
    code_wrap = _MDPOPUPS_HAVE_CODE_WRAP and view.settings().get('word_wrap')
    if code_wrap == 'auto':
        code_wrap = 'source.' not in view.scope_name(location)

    if highlight_diff:
        # (*) show a highlighted diff of the merged git and editor content
        new_lines = meta['added_lines']
        tab_width = view.settings().get('tab_width', 4)
        min_indent = _get_min_indent(deleted_lines + new_lines, tab_width)
        content = (
            '<div class="toolbar">'
            '{hide} '
            '{first_change} {prev_change} {next_change} '
            '{disable_hl_diff} {revert}'
            '</div>'
            .format(**buttons)
        ) + _highlight_diff(
            '\n'.join(line[min_indent:] for line in deleted_lines),
            '\n'.join(line[min_indent:] for line in new_lines))

    elif not is_added:
        # (modified/removed) show content from git database
        tab_width = view.settings().get('tab_width', 4)
        min_indent = _get_min_indent(deleted_lines, tab_width)
        source_content = '\n'.join(line[min_indent:] for line in deleted_lines)
        if not _MDPOPUPS_HAVE_FIXED_SPACE and not code_wrap:
            source_content = source_content.replace(' ', '\u00A0')
        # common arguments used to highlight the content
        popup_kwargs = {
            'language': mdpopups.get_language_from_view(view) or ''
        }
        # code wrapping is supported by mdpopups 2.0.0 or higher
        if _MDPOPUPS_HAVE_CODE_WRAP:
            popup_kwargs['allow_code_wrap'] = code_wrap
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
    }
    # code wrapping is supported by mdpopups 2.0.0 or higher
    if _MDPOPUPS_HAVE_CODE_WRAP:
        popup_kwargs['allow_code_wrap'] = code_wrap
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


def _built_toolbar_buttons(start, meta, use_icons):
    """Built the toolbar buttons with icon/text as link/label.

    Each toolbar button needs to be rendered using the unicode icon character
    or a text label for those who don't like icons. If enabled each button is
    attached to a <a> link.

    Arguments:
        start (int):
            First line of the current hunk.
        meta (dict):
            The dictionay containing additional hunk information.
        use_icons (bool):
            If True to use unicode buttons  or text otherwise.

    Returns:
        dict: The dictionay with all buttons where `key` is used as `href`
            and value as link caption.

            active icon button: <a href="revert"><symbol>⟲</symbol></a>
            active text button: <a href="revert"><text>(revert)</text></a>
            inactive icon button: <symbol>⟲</symbol>
            inactive text button: <text>(revert)</text>
    """
    # The format to render disabled/enabled buttons
    button_format = ('<{0}>{1}</{0}>', '<a href="{2}"><{0}>{1}</{0}></a>')
    # The tag to use for each button
    button_tag = ('text', 'symbol')
    # The buttons as a map from the href to the caption/icon
    button_caption = {
        'hide': ('(close)', '×'),
        'copy': ('(copy)', '⎘'),
        'revert': ('(revert)', '⟲'),
        'disable_hl_diff': ('(diff)', '≉'),
        'enable_hl_diff': ('(diff)', '≈'),
        'first_change': ('(first)', '⤒'),
        'prev_change': ('(prev)', '↑'),
        'next_change': ('(next)', '↓')
    }
    return {
        key: button_format[
            not key.endswith('_change') or meta.get(key, start) != start
        ].format(button_tag[use_icons], value[use_icons], key)
        for key, value in button_caption.items()
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

    # build the html string
    lines = ['<div class="highlight"><p>']
    for opcodes in seq_matcher.get_opcodes():
        op_type, git_start, git_end, edit_start, edit_end = opcodes
        if op_type == 'equal':
            lines.extend(_to_html(
                '', '', old_content[git_start:git_end]))
        elif op_type == 'delete':
            lines.extend(_to_html(
                '<span class="hi-del">', '</span>',
                old_content[git_start:git_end]))
        elif op_type == 'insert':
            lines.extend(_to_html(
                '<span class="hi-ins">', '</span>',
                new_content[edit_start:edit_end]))
        elif op_type == 'replace':
            lines.extend(_to_html(
                '<span class="hi-chg-del">', '</span>',
                old_content[git_start:git_end]))
            lines.extend(_to_html(
                '<span class="hi-chg-ins">', '</span>',
                new_content[edit_start:edit_end]))

    lines.append('</p></div>')
    # return markup string
    return ''.join(lines)


def _to_html(tag_start, tag_end, text):
    # escape basic html entities
    markup = html.escape(text, quote=False)
    # ensure display multiple whitespace
    markup = markup.replace('  ', '&nbsp;&nbsp;')
    # escape unbreakable whitespace
    if not _MDPOPUPS_HAVE_FIXED_SPACE:
        markup = markup.replace('\u00A0', '&nbsp;')
    # escape line feed in changed hunks
    if tag_start and tag_end:
        markup = markup.replace('\n', '↵\n')
    # Ignore the right most line feed because next replace would
    # add an empty region to the next line otherwise.
    if markup[-1] == '\n':
        markup = markup[:-1]
        tag_eol = '</p><p>'
    else:
        tag_eol = ''
    # escape remaining line feed
    markup = markup.replace('\n', ''.join((tag_end, '</p><p>', tag_start)))
    # wrap content into tags
    return (tag_start, markup, tag_end, tag_eol)


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
