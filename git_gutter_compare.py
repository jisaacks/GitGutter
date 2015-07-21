import sublime
import sublime_plugin
from functools import partial

ST3 = int(sublime.version()) >= 3000

if ST3:
    from .promise import Promise, ConstPromise
else:
    from promise import Promise, ConstPromise

class GitGutterCompareCommit:
    def __init__(self, view, git_handler, settings):
        self.view = view
        self.git_handler = git_handler
        self.settings = settings

    def run(self):
        def show_quick_panel(results):
            if results:
                self.view.window().show_quick_panel(results, partial(self.on_select, results))
        self.commit_list().addCallback(show_quick_panel)

    def commit_list(self):
        def decode_and_parse_commit_list(result):
            return [r.split('\a', 2) for r in result.decode("utf-8").strip().split('\n')]
        if self.git_handler.on_disk():
            return self.git_handler.git_commits().map(decode_and_parse_commit_list)
        else:
            return ConstPromise([])

    def item_to_commit(self, item):
        return item[1].split(' ')[0]

    def on_select(self, results, selected):
        if 0 > selected < len(results):
            return
        item = results[selected]
        commit = self.item_to_commit(item)
        self.settings.set_compare_against(self.git_handler.git_dir, commit)
        self.git_handler.clear_git_time()
        self.view.run_command('git_gutter') # refresh ui


class GitGutterCompareBranch(GitGutterCompareCommit):
    def commit_list(self):
        def decode_and_parse_branch_list(result):
            return [self.parse_result(r) for r in result.decode("utf-8").strip().split('\n')]
        if self.git_handler.on_disk():
            return self.git_handler.git_branches().map(decode_and_parse_branch_list)
        else:
            return ConstPromise([])

    def parse_result(self, result):
        pieces = result.split('\a')
        message = pieces[0]
        branch  = pieces[1].split("/",2)[2]
        commit  = pieces[2][0:7]
        return [branch, commit + " " + message]

class GitGutterCompareTag(GitGutterCompareCommit):
    def commit_list(self):
        def decode_and_parse_tag_list(result):
            if result:
                return [self.parse_result(r) for r in result.decode("utf-8").strip().split('\n')]
            else:
                sublime.message_dialog("No tags found in repository")
                return ConstPromise([])

        if self.git_handler.on_disk():
            return self.git_handler.git_tags().map(decode_and_parse_tag_list)
        else:
            return ConstPromise([])

    def parse_result(self, result):
        pieces = result.split(' ')
        commit = pieces[0]
        tag    = pieces[1].replace("refs/tags/", "")
        return [tag, commit]

    def item_to_commit(self, item):
        return item[1]

class GitGutterCompareHead(GitGutterCompareCommit):
    def run(self):
        self.settings.set_compare_against(self.git_handler.git_dir, 'HEAD')
        self.git_handler.clear_git_time()
        self.view.run_command('git_gutter') # refresh ui

class GitGutterCompareOrigin(GitGutterCompareCommit):
    def run(self):
        def on_branch_name(branch_name):
            if branch_name:
                self.settings.set_compare_against(self.git_handler.git_dir, 'origin/' + branch_name.decode("utf-8").strip())
                self.git_handler.clear_git_time()
                self.view.run_command('git_gutter') # refresh ui
        self.git_handler.git_current_branch().addCallback(on_branch_name)