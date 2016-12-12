from sublime_plugin import TextCommand

try:
    from .git_gutter_settings import settings
    from .git_gutter_handler import GitGutterHandler
    from .git_gutter_compare import (
        GitGutterCompareCommit, GitGutterCompareBranch, GitGutterCompareTag,
        GitGutterCompareHead, GitGutterCompareOrigin, GitGutterShowCompare)
    from .git_gutter_jump_to_changes import GitGutterJumpToChanges
    from .git_gutter_popup import show_diff_popup
    from .git_gutter_show_diff import GitGutterShowDiff
except (ImportError, ValueError):
    from git_gutter_settings import settings
    from git_gutter_handler import GitGutterHandler
    from git_gutter_compare import (
        GitGutterCompareCommit, GitGutterCompareBranch, GitGutterCompareTag,
        GitGutterCompareHead, GitGutterCompareOrigin, GitGutterShowCompare)
    from git_gutter_jump_to_changes import GitGutterJumpToChanges
    from git_gutter_popup import show_diff_popup
    from git_gutter_show_diff import GitGutterShowDiff


class GitGutterCommand(TextCommand):
    def __init__(self, *args, **kwargs):
        TextCommand.__init__(self, *args, **kwargs)
        self.git_handler = GitGutterHandler(self.view)
        self.show_diff_handler = GitGutterShowDiff(self.view, self.git_handler)

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
        # Don't handle views without valid file
        elif not self.git_handler.on_disk():
            valid = False
        # Don't handle files outside a repository
        elif not self.git_handler.git_dir:
            valid = False
        # Save state for use in other modules
        view.settings().set('git_gutter_enabled', valid)
        return valid

    def run(self, edit, **kwargs):
        """API entry point to run the `git_gutter` command."""
        if kwargs:
            self._handle_subcommand(**kwargs)
        else:
            self.show_diff_handler.run()

    def _handle_subcommand(self, **kwargs):
        view = self.view
        git_handler = self.git_handler
        action = kwargs['action']
        if action == 'jump_to_next_change':
            GitGutterJumpToChanges(view, git_handler).jump_to_next_change()
        elif action == 'jump_to_prev_change':
            GitGutterJumpToChanges(view, git_handler).jump_to_prev_change()
        elif action == 'compare_against_commit':
            GitGutterCompareCommit(view, git_handler).run()
        elif action == 'compare_against_branch':
            GitGutterCompareBranch(view, git_handler).run()
        elif action == 'compare_against_tag':
            GitGutterCompareTag(view, git_handler).run()
        elif action == 'compare_against_head':
            GitGutterCompareHead(view, git_handler).run()
        elif action == 'compare_against_origin':
            GitGutterCompareOrigin(view, git_handler).run()
        elif action == 'show_compare':
            GitGutterShowCompare(view, git_handler).run()
        elif action == 'show_diff_popup':
            point = kwargs['point']
            highlight_diff = kwargs['highlight_diff']
            flags = kwargs['flags']
            show_diff_popup(
                view, point, git_handler, highlight_diff=highlight_diff,
                flags=flags)
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
