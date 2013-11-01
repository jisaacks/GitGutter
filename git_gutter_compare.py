import sublime
import sublime_plugin

ST3 = int(sublime.version()) >= 3000
if ST3:
    from GitGutter.view_collection import ViewCollection
else:
    from view_collection import ViewCollection

class GitGutterCompareCommit(sublime_plugin.WindowCommand):
    def run(self):
        self.view = self.window.active_view()
        key = ViewCollection.get_key(self.view)
        self.handler = ViewCollection.views[key]

        self.results = self.commit_list()
        self.window.show_quick_panel(self.results, self.on_select)

    def commit_list(self):
        result = self.handler.git_commits().decode("utf-8")
        return [r.split('\a', 2) for r in result.strip().split('\n')]

    def item_to_commit(self, item):
        return item[1].split(' ')[0]

    def on_select(self, selected):
        if 0 > selected < len(self.results):
            return
        item = self.results[selected]
        commit = self.item_to_commit(item)
        ViewCollection.set_compare(commit)
        ViewCollection.clear_git_time(self.view)
        ViewCollection.add(self.view)

class GitGutterCompareBranch(GitGutterCompareCommit):
    def commit_list(self):
        result = self.handler.git_branches().decode("utf-8")
        return [self.parse_result(r) for r in result.strip().split('\n')]

    def parse_result(self, result):
        pieces = result.split('\a')
        message = pieces[0]
        branch  = pieces[1].split("/")[2]
        commit  = pieces[2][0:7]
        return [branch, commit + " " + message]

class GitGutterCompareTag(GitGutterCompareCommit):
    def commit_list(self):
        result = self.handler.git_tags().decode("utf-8")
        return [self.parse_result(r) for r in result.strip().split('\n')]

    def parse_result(self, result):
        if not result:
            sublime.message_dialog("No tags found in repository")
            return
        pieces = result.split(' ')
        commit = pieces[0]
        tag    = pieces[1].replace("refs/tags/", "")
        return [tag, commit]

    def item_to_commit(self, item):
        return item[1]

class GitGutterCompareHead(sublime_plugin.WindowCommand):
    def run(self):
        self.view = self.window.active_view()
        ViewCollection.set_compare("HEAD")
        ViewCollection.clear_git_time(self.view)
        ViewCollection.add(self.view)

class GitGutterShowCompare(sublime_plugin.WindowCommand):
    def run(self):
        comparing = ViewCollection.get_compare()
        sublime.message_dialog("GitGutter is comparing against: " + comparing)

