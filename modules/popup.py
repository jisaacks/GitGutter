# -*- coding: utf-8 -*-
import sublime
import sublime_plugin

try:
    if int(sublime.version()) < 3080:
        raise ImportError("No popup available.")

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
        git_gutter (GitGutterCommand): The main command object, which
            represents GitGutter.
        kwargs (dict): The arguments passed from GitGutterDiffPopupCommand
            to GitGutterCommand.
    """
    if not _MDPOPUPS_INSTALLED or not git_gutter.git_handler.in_repo():
        return
    # validate highlighting argument
    highlight_diff = kwargs['highlight_diff']
    if highlight_diff is None:
        mode = git_gutter.settings.get("diff_popup_default_mode", "")
        highlight_diff = mode == "diff"
    # get line number from text point
    line = git_gutter.view.rowcol(kwargs['point'])[0] + 1

    _show_diff_popup_impl(
        view=git_gutter.view, settings=git_gutter.settings, line=line,
        highlight_diff=highlight_diff, flags=kwargs['flags'],
        diff_info=git_gutter.git_handler.diff_line_change(line))


def _show_diff_popup_impl(
        view, settings, line, highlight_diff, flags, diff_info):
    (deleted_lines, start, size, meta) = diff_info
    if start == -1:
        return

    # extract the type of the hunk: removed, modified, (x)or added
    is_removed = size == 0
    is_modified = not is_removed and bool(deleted_lines)
    is_added = not is_removed and not is_modified

    def navigate(href):
        if href == "hide":
            view.hide_popup()
        elif href == "revert":
            new_text = "\n".join(deleted_lines)
            # (removed) if there is no text to remove, set the
            # region to the end of the line, where the hunk starts
            # and add a new line to the start of the text
            if is_removed:
                if start != 0:
                    # set the start and the end to the end of the start line
                    start_point = end_point = view.text_point(start, 0) - 1
                    # add a leading newline before inserting the text
                    new_text = "\n" + new_text
                else:
                    # (special handling for deleted at the start of the file)
                    # if we are before the start we need to set the start
                    # to 0 and add the newline behind the text
                    start_point = end_point = 0
                    new_text = new_text + "\n"
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
            replace_param = {
                "a": start_point,
                "b": end_point,
                "text": new_text
            }
            view.run_command("git_gutter_replace_text", replace_param)
            # hide the popup and update the gutter
            view.hide_popup()
            view.run_command("git_gutter")
        elif href in ["disable_hl_diff", "enable_hl_diff"]:
            do_diff = {
                "disable_hl_diff": False,
                "enable_hl_diff": True
            }.get(href)
            # show a diff popup with the same diff info
            _show_diff_popup_impl(
                view, settings, line, highlight_diff=do_diff, flags=0,
                diff_info=diff_info)
        elif href == "copy":
            sublime.set_clipboard("\n".join(deleted_lines))
            copy_message = "  ".join(l.strip() for l in deleted_lines)
            sublime.status_message("Copied: " + copy_message)
        elif href in ["next_change", "prev_change", "first_change"]:
            next_line = meta.get(href, line)
            pt = view.text_point(next_line - 1, 0)

            def show_new_popup():
                if view.visible_region().contains(pt):
                    popup_kwargs = {
                        'action': 'show_diff_popup',
                        'highlight_diff': highlight_diff,
                        'point': pt,
                        'flags': 0
                    }
                    view.run_command('git_gutter', popup_kwargs)
                else:
                    sublime.set_timeout(show_new_popup, 10)
            view.show_at_center(pt)
            show_new_popup()

    # write the symbols/text for each button
    use_icons = settings.get("diff_popup_use_icon_buttons")

    # the buttons as a map from the href to the caption/icon
    button_descriptions = {
        "hide": chr(0x00D7) if use_icons else "(close)",
        "copy": chr(0x2398) if use_icons else "(copy)",
        "revert": chr(0x27F2) if use_icons else "(revert)",
        "disable_hl_diff": chr(0x2249) if use_icons else "(diff)",
        "enable_hl_diff": chr(0x2248) if use_icons else "(diff)",
        "first_change": chr(0x2912) if use_icons else "(first)",
        "prev_change": chr(0x2191) if use_icons else "(previous)",
        "next_change": chr(0x2193) if use_icons else "(next)"
    }

    def is_button_enabled(k):
        if k in ["first_change", "next_change", "prev_change"]:
            return meta.get(k, start) != start
        return True
    buttons = {}
    for k, v in button_descriptions.items():
        if is_button_enabled(k):
            button = '<a href={1}>{0}</a>'.format(v, k)
        else:
            button = v
        buttons[k] = (
            '<span class="gitgutter-button">{0}</span>'
            .format(button)
        )

    if highlight_diff:
        # (*) show a highlighted diff of the merged git and editor content
        min_indent = _get_min_indent(deleted_lines + meta["added_lines"])

        old_content = "\n".join(l[min_indent:] for l in deleted_lines)
        new_content = "\n".join(l[min_indent:] for l in meta["added_lines"])
        source_html = _highlight_diff(old_content, new_content)

        button_line = (
            '{hide} '
            '{first_change} {prev_change} {next_change} '
            '{disable_hl_diff} {revert}'
            .format(**buttons)
        )
        content = (
            '{button_line}'
            '{source_html}'
            .format(**locals())
        )
    elif not is_added:
        # (modified/removed) show the button line above the content,
        # which in git
        lang = mdpopups.get_language_from_view(view) or ""
        # strip the indent to the minimal indentation
        is_tab_indent = any(l.startswith("\t") for l in deleted_lines)
        indent_char = "\t" if is_tab_indent else " "
        min_indent = _get_min_indent(deleted_lines)
        source_content = "\n".join(l[min_indent:] for l in deleted_lines)
        # replace spaces by non-breakable ones to avoid line wrapping
        # (this has been added to mdpopups in version 1.11.0)
        if mdpopups.version() < (1, 11, 0):
            source_content = source_content.replace(" ", "\u00A0")
        source_html = mdpopups.syntax_highlight(
            view, source_content, language=lang)
        button_line = (
            '{hide} '
            '{first_change} {prev_change} {next_change} '
            '{enable_hl_diff} {copy} {revert}'
            .format(**buttons)
        )
        content = (
            '{button_line}'
            '{source_html}'
            .format(**locals())
        )
    else:
        # (added) only show the button line without the copy button
        # (there is nothing to show or copy)
        button_line = (
            '{hide} '
            '{first_change} {prev_change} {next_change} '
            '{enable_hl_diff} {revert}'
            .format(**buttons)
        )
        content = button_line

    wrapper_class = ".git-gutter" if _MD_POPUPS_USE_WRAPPER_CLASS else ""

    # load and join popup stylesheets
    css = []
    theme_paths = (
        "Packages/GitGutter",
        settings.theme_path,
        "Packages/User"
    )
    for path in theme_paths:
        try:
            resource_name = path + "/gitgutter_popup.css"
            css.append(sublime.load_resource(resource_name))
        except IOError:
            pass

    # apply the jinja template
    jinja_kwargs = {
        "st_version": sublime.version(),
        "wrapper_class": wrapper_class,
        "use_icons": use_icons
    }
    tmpl = jinja2.environment.Template("\n".join(css))
    css = tmpl.render(**jinja_kwargs)
    # if the ST version does not support the wrapper class, remove it
    if not _MD_POPUPS_USE_WRAPPER_CLASS:
        css = css.replace(".git-gutter", "")

    # create the popup
    location = view.text_point(line - 1, 0)
    window_width = int(view.viewport_extent()[0])
    mdpopups.show_popup(
        view, content, location=location, on_navigate=navigate, md=False,
        wrapper_class=wrapper_class[1:], css=css,
        flags=flags, max_width=window_width)


def _get_min_indent(lines):
    is_tab_indent = any(l.startswith("\t") for l in lines)
    indent_char = "\t" if is_tab_indent else " "
    try:
        min_indent = min(len(l) - len(l.lstrip(indent_char))
                         for l in lines if l)
    except ValueError:
        min_indent = 0
    return min_indent


def _highlight_diff(old_content, new_content):
    seq_matcher = difflib.SequenceMatcher(None, old_content, new_content)
    tag_close = '</span>'

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
    sb = ['<div class="highlight">', '<pre>']
    for op in seq_matcher.get_opcodes():
        op_type, git_start, git_end, edit_start, edit_end = op
        if op_type == "equal":
            sb.append(tag_eq)
            sb.append(_to_html(old_content[git_start:git_end]))
            sb.append(tag_close)
        elif op_type == "delete":
            sb.append(tag_del)
            sb.append(_to_html(old_content[git_start:git_end]))
            sb.append(tag_close)
        elif op_type == "insert":
            sb.append(tag_ins)
            sb.append(_to_html(new_content[edit_start:edit_end]))
            sb.append(tag_close)
        elif op_type == "replace":
            sb.append(tag_modified_ins)
            sb.append(_to_html(new_content[edit_start:edit_end]))
            sb.append(tag_close)
            sb.append(tag_modified_del)
            sb.append(_to_html(old_content[git_start:git_end]))
            sb.append(tag_close)
    sb.extend(['</pre>', '</div>'])
    return "".join(sb)


def _to_html(s):
    return (
        html.escape(s, quote=False)
        .replace("\n", "<br>")
        .replace(" ", "&nbsp;")
        .replace("\u00A0", "&nbsp;")
    )


class GitGutterReplaceTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, a, b, text):
        region = sublime.Region(a, b)
        self.view.replace(edit, region, text)


class GitGutterDiffPopupCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return (
            _MDPOPUPS_INSTALLED and
            self.view.settings().get('git_gutter_is_enabled', False))

    def run(self, edit, point=None, highlight_diff=None, flags=0):
        if point is None:
            if not self.view.sel():
                return
            point = self.view.sel()[0].end()

        self.view.run_command('git_gutter', {
            'action': 'show_diff_popup', 'point': point,
            'highlight_diff': highlight_diff, 'flags': flags})
