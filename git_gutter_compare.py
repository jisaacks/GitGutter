from functools import partial

import sublime

try:
    from .git_gutter_settings import settings
    from .promise import Promise
except (ImportError, ValueError):
    from git_gutter_settings import settings
    from promise import Promise


class GitGutterCompareCommit(object):
    def __init__(self, view, git_handler):
        self.view = view
        self.git_handler = git_handler

    def run(self):
        self.commit_list().then(self._show_quick_panel)

    def commit_list(self):
        def decode_and_parse_commit_list(result):
            commit_lines = result.decode("utf-8").strip().split('\n')
            return [r.split('\a', 2) for r in commit_lines]
        if not self.git_handler.on_disk():
            return Promise.resolve([])
        return self.git_handler.git_commits().then(decode_and_parse_commit_list)

    def item_to_commit(self, item):
        return item[1].split(' ')[0]

    def _show_quick_panel(self, results):
        if results:
            self.view.window().show_quick_panel(
                results, partial(self._on_select, results))

    def _on_select(self, results, selected):
        if 0 > selected < len(results):
            return
        item = results[selected]
        commit = self.item_to_commit(item)
        settings.set_compare_against(commit)
        self.git_handler.clear_git_time()
        self.view.run_command('git_gutter')  # refresh ui


class GitGutterCompareBranch(GitGutterCompareCommit):
    def commit_list(self):
        def decode_and_parse_branch_list(result):
            branch_lines = result.decode("utf-8").strip().split('\n')
            return [self._parse_result(r) for r in branch_lines]
        if not self.git_handler.on_disk():
            return Promise.resolve([])
        return self.git_handler.git_branches().then(
            decode_and_parse_branch_list)

    def _parse_result(self, result):
        pieces = result.split('\a')
        message = pieces[0]
        branch  = pieces[1].split("/", 2)[2]
        commit  = pieces[2][0:7]
        return [branch, commit + " " + message]


class GitGutterCompareTag(GitGutterCompareCommit):
    def commit_list(self):
        def decode_and_parse_tag_list(results):
            if results:
                tag_lines = results.decode("utf-8").strip().split('\n')
                return [self._parse_result(r) for r in tag_lines]
            sublime.message_dialog("No tags found in repository")
            return []
        if not self.git_handler.on_disk():
            return Promise.resolve([])
        return self.git_handler.git_tags().then(decode_and_parse_tag_list)

    def _parse_result(self, result):
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
        def on_branch_name(branch_name):
            if branch_name:
                settings.set_compare_against(
                    'origin/%s' % branch_name.decode("utf-8").strip())
                self.git_handler.clear_git_time()
                self.view.run_command('git_gutter')  # refresh ui
        self.git_handler.git_current_branch().then(on_branch_name)


class GitGutterShowCompare(GitGutterCompareCommit):
    def run(self):
        comparing = settings.get_compare_against(self.view)
        sublime.message_dialog('GitGutter is comparing against: %s' % comparing)
