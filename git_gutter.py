import sublime_plugin

try:
    from .git_gutter_handler import GitGutterHandler
    from .git_gutter_compare import (
        GitGutterCompareCommit, GitGutterCompareBranch, GitGutterCompareTag,
        GitGutterCompareHead, GitGutterCompareOrigin, GitGutterShowCompare)
    from .git_gutter_jump_to_changes import GitGutterJumpToChanges
    from .git_gutter_popup import show_diff_popup
    from .git_gutter_show_diff import GitGutterShowDiff
except (ImportError, ValueError):
    from git_gutter_handler import GitGutterHandler
    from git_gutter_compare import (
        GitGutterCompareCommit, GitGutterCompareBranch, GitGutterCompareTag,
        GitGutterCompareHead, GitGutterCompareOrigin, GitGutterShowCompare)
    from git_gutter_jump_to_changes import GitGutterJumpToChanges
    from git_gutter_popup import show_diff_popup
    from git_gutter_show_diff import GitGutterShowDiff


class GitGutterCommand(sublime_plugin.TextCommand):
    def __init__(self, *args, **kwargs):
        sublime_plugin.TextCommand.__init__(self, *args, **kwargs)
        self.is_valid_view = self.view.settings().get('is_widget') is not True
        self.git_handler = None
        self.show_diff_handler = None

    def is_enabled(self, **kwargs):
        return self.is_valid_view

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


class GitGutterShowCompareCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command('git_gutter', {'action': 'show_compare'})


class GitGutterCompareHeadCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command('git_gutter', {'action': 'compare_against_head'})


class GitGutterCompareOriginCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command(
            'git_gutter', {'action': 'compare_against_origin'})


class GitGutterCompareCommitCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command(
            'git_gutter', {'action': 'compare_against_commit'})


class GitGutterCompareBranchCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command(
            'git_gutter', {'action': 'compare_against_branch'})


class GitGutterCompareTagCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command(
            'git_gutter', {'action': 'compare_against_tag'})


class GitGutterNextChangeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command('git_gutter', {'action': 'jump_to_next_change'})


class GitGutterPrevChangeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.run_command('git_gutter', {'action': 'jump_to_prev_change'})
