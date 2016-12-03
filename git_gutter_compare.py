from functools import partial

import sublime


class GitGutterCompareCommit(object):
    def __init__(self, git_handler):
        self.git_handler = git_handler

    def run(self):
        self.commit_list().then(self._show_quick_panel)

    def commit_list(self):
        """Built a list of quick panel items with all commits."""
        def parse_results(results):
            """Parse git output and create the quick panel items."""
            if results:
                return [r.split('\a') for r in results.splitlines()]
            sublime.message_dialog('No commits found in repository.')
            return []
        return self.git_handler.git_commits().then(parse_results)

    def item_to_commit(self, item):
        return item[1].split(' ')[0]

    def _show_quick_panel(self, results):
        if results:
            self.git_handler.view.window().show_quick_panel(
                results, partial(self._on_select, results))

    def _on_select(self, results, selected):
        if 0 > selected < len(results):
            return
        item = results[selected]
        commit = self.item_to_commit(item)
        self.git_handler.set_compare_against(commit)


class GitGutterCompareBranch(GitGutterCompareCommit):
    def commit_list(self):
        """Built a list of quick panel items with all local branches."""
        def parse_result(result):
            """Create a quick panel item for one line of git's output."""
            pieces = result.split('\a')
            message = pieces[0]
            branch = pieces[1][11:]   # skip 'refs/heads/'
            commit = pieces[2][0:7]   # 7-digit commit hash
            return [branch, '%s %s' % (commit, message)]

        def parse_results(results):
            """Parse git output and create the quick panel items."""
            if results:
                return [parse_result(r) for r in results.splitlines()]
            sublime.message_dialog('No branches found in repository.')
            return []
        return self.git_handler.git_branches().then(parse_results)

    def item_to_commit(self, item):
        return 'refs/heads/%s' % item[0]


class GitGutterCompareTag(GitGutterCompareCommit):
    def commit_list(self):
        """Built a list of quick panel items with all tags."""
        def parse_result(result):
            """Create a quick panel item for one line of git's output."""
            pieces = result.split(' ')
            commit = pieces[0]     # 7-digit commit hash
            tag = pieces[1][10:]   # skip 'refs/tags/'
            return [tag, commit]

        def parse_results(results):
            """Parse git output and create the quick panel items."""
            if results:
                return [parse_result(r) for r in results.splitlines()]
            sublime.message_dialog('No tags found in repository.')
            return []
        return self.git_handler.git_tags().then(parse_results)

    def item_to_commit(self, item):
        return 'refs/tags/%s' % item[0]


class GitGutterCompareHead(GitGutterCompareCommit):
    def run(self):
        self.git_handler.set_compare_against('HEAD', True)


class GitGutterCompareOrigin(GitGutterCompareCommit):
    def run(self):
        def on_branch_name(branch_name):
            if branch_name:
                self.git_handler.set_compare_against(
                    'origin/%s' % branch_name, True)
        self.git_handler.git_current_branch().then(on_branch_name)


class GitGutterShowCompare(GitGutterCompareCommit):
    def run(self):
        comparing = self.git_handler.format_compare_against()
        sublime.message_dialog(
            'GitGutter is comparing against: %s' % comparing)
