# -*- coding: utf-8 -*-
import sublime_plugin

try:
    from .git_gutter_handler import GitGutterHandler
    from .git_gutter_compare import (
        GitGutterCompareCommit, GitGutterCompareBranch, GitGutterCompareTag,
        GitGutterCompareHead, GitGutterCompareOrigin, GitGutterShowCompare,
        GitGutterCompareFileCommit)
    from .git_gutter_popup import show_diff_popup
    from .git_gutter_show_diff import GitGutterShowDiff
    from .modules import events
    from .modules import goto
    from .modules import settings
except ValueError:
    from git_gutter_handler import GitGutterHandler
    from git_gutter_compare import (
        GitGutterCompareCommit, GitGutterCompareBranch, GitGutterCompareTag,
        GitGutterCompareHead, GitGutterCompareOrigin, GitGutterShowCompare,
        GitGutterCompareFileCommit)
    from git_gutter_popup import show_diff_popup
    from git_gutter_show_diff import GitGutterShowDiff
    from modules import events
    from modules import goto
    from modules import settings


class GitGutterCommand(sublime_plugin.TextCommand):
    def __init__(self, *args, **kwargs):
        """Initialize GitGutterCommand object."""
        sublime_plugin.TextCommand.__init__(self, *args, **kwargs)
        self.settings = settings.ViewSettings(self.view)
        self.git_handler = GitGutterHandler(self.view, self.settings)
        self.show_diff_handler = GitGutterShowDiff(self.git_handler)
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
            # Validate work tree on certain events only
            validate = kwargs.get('events', 0) & (
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
        if 'action' in kwargs:
            self._handle_subcommand(**kwargs)
        else:
            self._handle_event(**kwargs)

    def _handle_event(self, **kwargs):
        queued_events = kwargs.get('events', 0)
        if not queued_events & (events.LOAD | events.MODIFIED):
            # On 'load' the git file is not yet valid anyway.
            # On 'modified' is sent when user is typing.
            # The git repository will most likely not change then.
            self.git_handler.invalidate_git_file()
        self.show_diff_handler.run()

    def _handle_subcommand(self, **kwargs):
        action = kwargs['action']
        if action == 'jump_to_next_change':
            goto.next_change(self)
        elif action == 'jump_to_prev_change':
            goto.prev_change(self)
        elif action == 'compare_against_commit':
            GitGutterCompareCommit(self.git_handler).run()
        elif action == 'compare_against_file_commit':
            GitGutterCompareFileCommit(self.git_handler).run()
        elif action == 'compare_against_branch':
            GitGutterCompareBranch(self.git_handler).run()
        elif action == 'compare_against_tag':
            GitGutterCompareTag(self.git_handler).run()
        elif action == 'compare_against_head':
            GitGutterCompareHead(self.git_handler).run()
        elif action == 'compare_against_origin':
            GitGutterCompareOrigin(self.git_handler).run()
        elif action == 'show_compare':
            GitGutterShowCompare(self.git_handler).run()
        elif action == 'show_diff_popup':
            show_diff_popup(self, **kwargs)
        else:
            assert False, 'Unhandled sub command "%s"' % action


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
