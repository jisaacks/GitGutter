# -*- coding: utf-8 -*-
import sublime_plugin

from . import compare
from . import events
from . import goto
from . import handler
from . import popup
from . import settings
from . import show_diff


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
        'show_diff_popup': popup.show_diff_popup
    }

    def __init__(self, *args, **kwargs):
        """Initialize GitGutterCommand object."""
        sublime_plugin.TextCommand.__init__(self, *args, **kwargs)
        self.settings = settings.ViewSettings(self.view)
        self.git_handler = handler.GitGutterHandler(self.view, self.settings)
        self.show_diff_handler = show_diff.GitGutterShowDiff(self.git_handler)
        # Last enabled state for change detection
        self._enabled = False

    def is_enabled(self, **kwargs):
        """Determine if `git_gutter` command is _enabled to execute."""
        view = self.view
        valid = True

        # Keep idle, if disabled by user setting
        if not self.settings.get('enable'):
            valid = False
        # Don't handle unattached views
        elif not view.window():
            valid = False
        # Don't handle scratch or readonly views
        elif view.is_scratch() or view.is_read_only():
            valid = False
        # Don't handle widgets
        elif view.settings().get('is_widget'):
            valid = False
        # Don't handle SublimeREPL views
        elif view.settings().get("repl"):
            valid = False
        # Don't handle binary files
        elif view.encoding() == 'Hexadecimal':
            valid = False
        else:
            queued_events = kwargs.get('events')
            # Validate work tree on certain events only
            validate = queued_events is None or queued_events & (
                events.LOAD | events.ACTIVATED | events.POST_SAVE)
            # Don't handle files outside a repository
            if not self.git_handler.work_tree(validate):
                valid = False

        # Handle changed state
        if valid != self._enabled:
            # File moved out of work-tree or repository gone
            if not valid:
                self.show_diff_handler.clear()
                self.git_handler.invalidate_view_file()
            # Save state for use in other modules
            view.settings().set('git_gutter_is_enabled', valid)
            # Save state for internal use
            self._enabled = valid
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
    def is_enabled(self, **kwargs):
        return self.view.settings().get('git_gutter_is_enabled', False)


class GitGutterShowCompareCommand(GitGutterBaseCommand):
    def run(self, edit):
        self.view.run_command('git_gutter', {'action': 'show_compare'})


class GitGutterCompareHeadCommand(GitGutterBaseCommand):
    def run(self, edit):
        self.view.run_command('git_gutter', {'action': 'compare_against_head'})


class GitGutterCompareOriginCommand(GitGutterBaseCommand):
    def run(self, edit):
        self.view.run_command(
            'git_gutter', {'action': 'compare_against_origin'})


class GitGutterCompareCommitCommand(GitGutterBaseCommand):
    def run(self, edit):
        self.view.run_command(
            'git_gutter', {'action': 'compare_against_commit'})


class GitGutterCompareFileCommitCommand(GitGutterBaseCommand):
    def run(self, edit):
        self.view.run_command(
            'git_gutter', {'action': 'compare_against_file_commit'})


class GitGutterCompareBranchCommand(GitGutterBaseCommand):
    def run(self, edit):
        self.view.run_command(
            'git_gutter', {'action': 'compare_against_branch'})


class GitGutterCompareTagCommand(GitGutterBaseCommand):
    def run(self, edit):
        self.view.run_command('git_gutter', {'action': 'compare_against_tag'})


class GitGutterNextChangeCommand(GitGutterBaseCommand):
    def run(self, edit):
        self.view.run_command('git_gutter', {'action': 'jump_to_next_change'})


class GitGutterPrevChangeCommand(GitGutterBaseCommand):
    def run(self, edit):
        self.view.run_command('git_gutter', {'action': 'jump_to_prev_change'})
