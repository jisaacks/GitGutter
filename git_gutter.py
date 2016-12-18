from sublime_plugin import TextCommand

try:
    from .git_gutter_settings import settings
    from .git_gutter_handler import GitGutterHandler
    from .git_gutter_compare import (
        GitGutterCompareCommit, GitGutterCompareBranch, GitGutterCompareTag,
        GitGutterCompareHead, GitGutterCompareOrigin, GitGutterShowCompare,
        GitGutterCompareFileCommit)
    from .git_gutter_jump_to_changes import GitGutterJumpToChanges
    from .git_gutter_popup import show_diff_popup
    from .git_gutter_show_diff import GitGutterShowDiff
except (ImportError, ValueError):
    from git_gutter_settings import settings
    from git_gutter_handler import GitGutterHandler
    from git_gutter_compare import (
        GitGutterCompareCommit, GitGutterCompareBranch, GitGutterCompareTag,
        GitGutterCompareHead, GitGutterCompareOrigin, GitGutterShowCompare,
        GitGutterCompareFileCommit)
    from git_gutter_jump_to_changes import GitGutterJumpToChanges
    from git_gutter_popup import show_diff_popup
    from git_gutter_show_diff import GitGutterShowDiff


class GitGutterCommand(TextCommand):
    def __init__(self, *args, **kwargs):
        TextCommand.__init__(self, *args, **kwargs)
        self.git_handler = GitGutterHandler(self.view)
        self.show_diff_handler = GitGutterShowDiff(self.view, self.git_handler)
        # Last enabled state for change detection
        self._enabled = False

    def is_enabled(self, **kwargs):
        """Determine if `git_gutter` command is _enabled to execute."""
        view = self.view
        valid = True
        # Keep idle, if git binary is not set
        if not settings.git_binary_path:
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
        elif view.encoding() in ('Hexadecimal'):
            valid = False
        # Don't handle files outside a repository
        elif not self.git_handler.work_tree(validate=True):
            valid = False
        # Handle changed state
        if valid != self._enabled:
            # File moved out of work-tree or repository gone
            if not valid:
                self.show_diff_handler.clear()
            # Save state for use in other modules
            view.settings().set('git_gutter_enabled', valid)
            # Save state for internal use
            self._enabled = valid
        return valid

    def run(self, edit, **kwargs):
        """API entry point to run the `git_gutter` command."""
        if kwargs:
            self._handle_subcommand(**kwargs)
        else:
            self.show_diff_handler.run()

    def _handle_subcommand(self, **kwargs):
        action = kwargs['action']
        if action == 'jump_to_next_change':
            GitGutterJumpToChanges(self.git_handler).jump_to_next_change()
        elif action == 'jump_to_prev_change':
            GitGutterJumpToChanges(self.git_handler).jump_to_prev_change()
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
            point = kwargs['point']
            highlight_diff = kwargs['highlight_diff']
            flags = kwargs['flags']
            show_diff_popup(
                point, self.git_handler,
                highlight_diff=highlight_diff, flags=flags)
        else:
            assert False, 'Unhandled sub command "%s"' % action


class GitGutterBaseCommand(TextCommand):
    def is_enabled(self, **kwargs):
        return self.view.settings().get('git_gutter_enabled', False)


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
