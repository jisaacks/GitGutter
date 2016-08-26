import sublime
import sublime_plugin

try:
    _MDPOPUPS_INSTALLED = True
    import mdpopups
    # to be sure check, that ST also support popups
    if int(sublime.version()) < 3080:
        _MDPOPUPS_INSTALLED = False
except:
    _MDPOPUPS_INSTALLED = False

try:
    from .view_collection import ViewCollection
except (ImportError, ValueError):
    from view_collection import ViewCollection

ST3 = int(sublime.version()) >= 3000
_MD_POPUPS_USE_WRAPPER_CLASS = int(sublime.version()) >= 3119


def plugin_loaded():
    global settings
    settings = sublime.load_settings('GitGutter.sublime-settings')


def show_diff_popup(view, point, flags=0):
    if not _MDPOPUPS_INSTALLED:
        return

    line = view.rowcol(point)[0] + 1
    lines, start, size, meta = ViewCollection.diff_line_change(view, line)
    if start == -1:
        return

    # extract the type of the hunk: removed, modified, (x)or added
    is_removed = size == 0
    is_modified = not is_removed and bool(lines)
    is_added = not is_removed and not is_modified

    def navigate(href):
        if href == "hide":
            view.hide_popup()
        elif href == "revert":
            new_text = "\n".join(lines)
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
            view.window().run_command("git_gutter")
        elif href == "copy":
            sublime.set_clipboard("\n".join(lines))
            copy_message = "  ".join(l.strip() for l in lines)
            sublime.status_message("Copied: " + copy_message)
        elif href in ["next_change", "prev_change", "first_change"]:
            next_line = meta.get(href, line)
            pt = view.text_point(next_line - 1, 0)

            def show_new_popup():
                if view.visible_region().contains(pt):
                    show_diff_popup(view, pt, flags=flags)
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
            buttons[k] = '[{0}]({1})'.format(v, k)
        else:
            buttons[k] = v

    if not is_added:
        # (modified/removed) show the button line above the content,
        # which in git
        lang = mdpopups.get_language_from_view(view) or ""
        # strip the indent to the minimal indentation
        is_tab_indent = any(l.startswith("\t") for l in lines)
        indent_char = "\t" if is_tab_indent else " "
        min_indent = min(len(l) - len(l.lstrip(indent_char))
                         for l in lines)
        source_content = "\n".join(l[min_indent:] for l in lines)
        # replace spaces by non-breakable ones to avoid line wrapping
        source_content = source_content.replace(" ", "\u00A0")
        button_line = (
            '{hide} '
            '{first_change} {prev_change} {next_change} '
            '{copy} {revert}'
            .format(**buttons)
        )
        content = (
            '{button_line}\n'
            '``` {lang}\n'
            '{source_content}\n'
            '```'
            .format(**locals())
        )
    else:
        # (added) only show the button line without the copy button
        # (there is nothing to show or copy)
        button_line = (
            '{hide} '
            '{first_change} {prev_change} {next_change} '
            '{revert}'
            .format(**buttons)
        )
        content = button_line
    css = ''
    if _MD_POPUPS_USE_WRAPPER_CLASS:
        wrapper_class = "git-gutter"
        if use_icons:
            css = 'div.git-gutter a { text-decoration: none; }'
    else:
        wrapper_class = ""
        if use_icons:
            css = 'a { text-decoration: none; }'
    location = view.line(point).a
    window_width = int(view.viewport_extent()[0])
    mdpopups.show_popup(
        view, content, location=location, on_navigate=navigate,
        wrapper_class=wrapper_class, css=css,
        flags=flags, max_width=window_width)


class GitGutterReplaceTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, a, b, text):
        region = sublime.Region(a, b)
        self.view.replace(edit, region, text)


class GitGutterDiffPopupCommand(sublime_plugin.WindowCommand):
    def is_enabled(self):
        if not _MDPOPUPS_INSTALLED:
            return False
        return True

    def run(self):
        view = self.window.active_view()
        if len(view.sel()) == 0:
            return
        point = view.sel()[0].b
        show_diff_popup(view, point, flags=0)


if not ST3:
    plugin_loaded()
