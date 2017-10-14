# -*- coding: utf-8 -*-
import os

import sublime
import sublime_plugin

from . import compare
from . import copy
from . import events
from . import goto
from . import handler
from . import popup
from . import revert
from . import settings
from . import show_diff
from . import utils

# the reason why evaluation is skipped, which is printed to console
# if debug is set true and evaluation.
DISABLED_REASON = {
    1: 'disabled in settings',
    2: 'view is transient',
    3: 'view is scratch',
    4: 'view is readonly',
    5: 'view is a widget',
    6: 'view is a REPL',
    7: 'view encoding is Hexadecimal',
    8: 'file not in a working tree',
    9: 'git is not working'
}


class GitGutterCommand(sublime_plugin.TextCommand):

    # The map of sub commands and their implementation
    commands = {
        'jump_to_next_change': goto.next_change,
        'jump_to_prev_change': goto.prev_change,
        'compare_against_commit': compare.set_against_commit,
        'compare_against_file_commit': compare.set_against_file_commit,
        'compare_against_branch': compare.set_against_branch,
        'compare_against_tag': compare.set_against_tag,
        'compare_against_head': compare.set_against_head,
        'compare_against_origin': compare.set_against_origin,
        'show_compare': compare.show_compare,
        'show_diff_popup': popup.show_diff_popup,
        'copy_from_commit': copy.copy_from_commit,
        'revert_change': revert.revert_change
    }

    def __init__(self, *args, **kwargs):
        """Initialize GitGutterCommand object."""
        sublime_plugin.TextCommand.__init__(self, *args, **kwargs)
        self.settings = settings.ViewSettings(self.view)
        self.git_handler = handler.GitGutterHandler(self.view, self.settings)
        self.show_diff_handler = show_diff.GitGutterShowDiff(self.git_handler)
        # Last enabled state for change detection
        self._state = -1

    def is_enabled(self, **kwargs):
        """Determine if `git_gutter` command is _enabled to execute."""
        view = self.view
        state = 0

        # Keep idle, if disabled by user setting
        if not self.settings.get('enable', True):
            state = 1
        # Don't handle unattached views
        elif not view.window():
            state = 2
        # Don't handle scratch views
        elif view.is_scratch():
            state = 3
        # Don't handle readonly views
        elif view.is_read_only():
            state = 4
        # Don't handle widgets
        elif view.settings().get('is_widget'):
            state = 5
        # Don't handle SublimeREPL views
        elif view.settings().get("repl"):
            state = 6
        # Don't handle binary files
        elif view.encoding() == 'Hexadecimal':
            state = 7
        else:
            queued_events = kwargs.get('events')
            # Validate work tree on certain events only
            validate = queued_events is None or queued_events & (
                events.LOAD | events.ACTIVATED | events.POST_SAVE)
            # Don't handle files outside a repository
            if not self.git_handler.work_tree(validate):
                state = 8
            # Keep quite if git is not working properly
            elif not self.git_handler.version(validate):
                state = 9

        # Handle changed state
        valid = state == 0
        if self._state != state:
            # File moved out of work-tree or repository gone
            if not valid:
                self.show_diff_handler.clear()
                self.git_handler.invalidate_view_file()
                if settings.get('debug'):
                    utils.log_message('disabled for "%s" because %s' % (
                        os.path.basename(self.view.file_name() or 'untitled'),
                        DISABLED_REASON[state]))
            # Save state for use in other modules
            view.settings().set('git_gutter_is_enabled', valid)
            # Save state for internal use
            self._state = state
        return valid

    def run(self, edit, **kwargs):
        """API entry point to run the `git_gutter` command."""
        action = kwargs.get('action')
        if action:
            command_func = self.commands.get(action)
            assert command_func, 'Unhandled sub command "%s"' % action
            return command_func(self, **kwargs)

        queued_events = kwargs.get('events', 0)
        if not queued_events & (events.LOAD | events.MODIFIED):
            # On 'load' the git file is not yet valid anyway.
            # On 'modified' is sent when user is typing.
            # The git repository will most likely not change then.
            self.git_handler.invalidate_git_file()
        self.show_diff_handler.run()


class GitGutterBaseCommand(sublime_plugin.TextCommand):
    """The base command proxies all commands to the git_gutter command."""

    # The action to proxy to git_gutter command.
    ACTION = ''

    def is_enabled(self, **kwargs):
        return self.view.settings().get('git_gutter_is_enabled', False)

    def run(self, edit, **kwargs):
        kwargs['action'] = self.ACTION
        self.view.run_command('git_gutter', kwargs)


class GitGutterShowCompareCommand(GitGutterBaseCommand):
    ACTION = 'show_compare'


class GitGutterCompareHeadCommand(GitGutterBaseCommand):
    ACTION = 'compare_against_head'


class GitGutterCompareOriginCommand(GitGutterBaseCommand):
    ACTION = 'compare_against_origin'


class GitGutterCompareCommitCommand(GitGutterBaseCommand):
    ACTION = 'compare_against_commit'


class GitGutterCompareFileCommitCommand(GitGutterBaseCommand):
    ACTION = 'compare_against_file_commit'


class GitGutterCompareBranchCommand(GitGutterBaseCommand):
    ACTION = 'compare_against_branch'


class GitGutterCompareTagCommand(GitGutterBaseCommand):
    ACTION = 'compare_against_tag'


class GitGutterNextChangeCommand(GitGutterBaseCommand):
    ACTION = 'jump_to_next_change'


class GitGutterPrevChangeCommand(GitGutterBaseCommand):
    ACTION = 'jump_to_prev_change'


class GitGutterCopyFromCommitCommand(GitGutterBaseCommand):
    ACTION = 'copy_from_commit'


class GitGutterRevertChangeCommand(GitGutterBaseCommand):
    ACTION = 'revert_change'


class GitGutterDiffPopupCommand(GitGutterBaseCommand):
    """The git_gutter_diff_popup command implemention."""
    ACTION = 'show_diff_popup'

    def is_enabled(self):
        """Enable command if mdpopups is available."""
        return self.is_visible() and GitGutterBaseCommand.is_enabled(self)

    def is_visible(self):
        """Show command in main menu only if mdpopups is available."""
        return popup.show_diff_popup is not None

    def run(self, edit, point=None, highlight_diff=None, flags=0):
        """Run git_gutter(show_diff_popup, ...) command.

        Note:
            Don't use run() of the base class to explicitly pusblish
            the command parameters.

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
            'action': self.ACTION, 'point': point,
            'highlight_diff': highlight_diff, 'flags': flags})


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


class GitGutterEnableViewCommand(sublime_plugin.TextCommand):

    def is_checked(self):
        """Return check mark state for menu items."""
        return self.view.settings().get('git_gutter_enable', True)

    def is_visible(self, enabled=None):
        """The command is visible if it would change the setting.

        Arguments:
            enabled (bool):
                The desired state of GitGutter if True or False.
                If none the current state is toggled.
        """
        return enabled is None or enabled != self.is_checked()

    def run(self, edit, enabled=None):
        """Enable or disable GitGutter.

        Arguments:
            edit (sublime.Edit):
                not used.
            enabled (bool):
                The desired state of GitGutter if True or False.
                If none the current state is toggled.
        """
        if enabled is None:
            enabled = not self.is_checked()
        self.view.settings().set('git_gutter_enable', enabled)
        self.view.run_command('git_gutter')
