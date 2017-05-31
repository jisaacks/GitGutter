# -*- coding: utf-8 -*-
"""Sublime Text Command Objects

All command objects required by diff popup are defined here.
"""
import sublime
import sublime_plugin


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
        visible_region = self.view.visible_region()
        region = sublime.Region(start, end)
        self.view.replace(edit, region, text)
        if start < visible_region.begin():
            self.view.show_at_center(start)
        self.view.sel().clear()
        self.view.sel().add(start)


class GitGutterDiffPopupCommand(sublime_plugin.TextCommand):
    """The git_gutter_diff_popup command implemention."""

    def is_enabled(self):
        """Check whether diff popup is enabled for the view."""
        return self.view.settings().get('git_gutter_is_enabled', False)

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
