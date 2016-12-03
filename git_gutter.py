from sublime_plugin import TextCommand

try:
    from .git_gutter_handler import GitGutterHandler
    from .git_gutter_compare import (
        GitGutterCompareCommit, GitGutterCompareBranch, GitGutterCompareTag,
        GitGutterCompareHead, GitGutterCompareOrigin, GitGutterShowCompare,
        GitGutterCompareFileCommit)
    from .git_gutter_jump_to_changes import GitGutterJumpToChanges
    from .git_gutter_popup import show_diff_popup
    from .git_gutter_show_diff import GitGutterShowDiff
except (ImportError, ValueError):
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
        """Initialize `git_gutter` command object."""
        TextCommand.__init__(self, *args, **kwargs)
        self.is_valid_view = self.view.settings().get('is_widget') is not True
        self.git_handler = None
        self.show_diff_handler = None

    def is_enabled(self, **kwargs):
        """Determine if `git_gutter` command is enabled to execute."""
        is_enabled = self.is_valid_view
        if is_enabled:
            # Don't handle scratch views
            is_enabled = self.view.is_scratch() is not True
        if is_enabled:
            # Don't handle binary files
            is_enabled = self.view.encoding() not in ('Hexadecimal')
        return is_enabled

    def run(self, edit, **kwargs):
        if not self.git_handler:
            self.git_handler = GitGutterHandler(self.view)
        if not self.show_diff_handler:
            self.show_diff_handler = GitGutterShowDiff(
                self.view, self.git_handler)

        if not self.git_handler.on_disk() or not self.git_handler.git_dir:
            return

        if kwargs:
            self._handle_subcommand(**kwargs)
            return

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


class GitGutterShowCompareCommand(TextCommand):
    def run(self, edit):
        self.view.run_command(
            'git_gutter', {'action': 'show_compare'})


class GitGutterCompareHeadCommand(TextCommand):
    def run(self, edit):
        self.view.run_command(
            'git_gutter', {'action': 'compare_against_head'})


class GitGutterCompareOriginCommand(TextCommand):
    def run(self, edit):
        self.view.run_command(
            'git_gutter', {'action': 'compare_against_origin'})


class GitGutterCompareCommitCommand(TextCommand):
    def run(self, edit):
        self.view.run_command(
            'git_gutter', {'action': 'compare_against_commit'})


class GitGutterCompareFileCommitCommand(TextCommand):
    def run(self, edit):
        self.view.run_command(
            'git_gutter', {'action': 'compare_against_file_commit'})


class GitGutterCompareBranchCommand(TextCommand):
    def run(self, edit):
        self.view.run_command(
            'git_gutter', {'action': 'compare_against_branch'})


class GitGutterCompareTagCommand(TextCommand):
    def run(self, edit):
        self.view.run_command(
            'git_gutter', {'action': 'compare_against_tag'})


class GitGutterNextChangeCommand(TextCommand):
    def run(self, edit):
        self.view.run_command(
            'git_gutter', {'action': 'jump_to_next_change'})


class GitGutterPrevChangeCommand(TextCommand):
    def run(self, edit):
        self.view.run_command(
            'git_gutter', {'action': 'jump_to_prev_change'})
