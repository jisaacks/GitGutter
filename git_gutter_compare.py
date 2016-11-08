import sublime
from functools import partial

try:
    from .git_gutter_settings import settings
except (ImportError, ValueError):
    from git_gutter_settings import settings


class GitGutterCompareCommit(object):
    def __init__(self, view, git_handler):
        self.view = view
        self.git_handler = git_handler

    def run(self):
        results = self.commit_list()
        if results:
            self.view.window().show_quick_panel(
                results, partial(self.on_select, results))

    def commit_list(self):
        result = self.git_handler.git_commits().decode("utf-8")
        return [r.split('\a', 2) for r in result.strip().split('\n')]

    def item_to_commit(self, item):
        return item[1].split(' ')[0]

    def on_select(self, results, selected):
        if 0 > selected < len(results):
            return
        item = results[selected]
        commit = self.item_to_commit(item)
        settings.set_compare_against(commit)
        self.git_handler.clear_git_time()
        self.view.run_command('git_gutter')  # refresh ui


class GitGutterCompareBranch(GitGutterCompareCommit):
    def commit_list(self):
        result = self.git_handler.git_branches().decode("utf-8")
        return [self.parse_result(r) for r in result.strip().split('\n')]

    def parse_result(self, result):
        pieces = result.split('\a')
        message = pieces[0]
        branch  = pieces[1].split("/", 2)[2]
        commit  = pieces[2][0:7]
        return [branch, commit + " " + message]


class GitGutterCompareTag(GitGutterCompareCommit):
    def commit_list(self):
        result = self.git_handler.git_tags().decode("utf-8")
        if result:
            return [self.parse_result(r) for r in result.strip().split('\n')]
        else:
            sublime.message_dialog("No tags found in repository")

    def parse_result(self, result):
        pieces = result.split(' ')
        commit = pieces[0]
        tag    = pieces[1].replace("refs/tags/", "")
        return [tag, commit]

    def item_to_commit(self, item):
        return item[1]


class GitGutterCompareHead(GitGutterCompareCommit):
    def run(self):
        settings.set_compare_against('HEAD')
        self.git_handler.clear_git_time()
        self.view.run_command('git_gutter')  # refresh ui


class GitGutterCompareOrigin(GitGutterCompareCommit):
    def run(self):
        branch_name = self.git_handler.git_current_branch()
        if branch_name:
            settings.set_compare_against(
                'origin/%s' % branch_name.decode("utf-8").strip())
            self.git_handler.clear_git_time()
            self.view.run_command('git_gutter')  # refresh ui


class GitGutterShowCompare(GitGutterCompareCommit):
    def run(self):
        comparing = settings.get_compare_against(self.view)
        sublime.message_dialog('GitGutter is comparing against: %s' % comparing)
