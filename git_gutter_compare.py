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
        handler = ViewCollection.views[key]

        result = handler.git_commits().decode("utf-8")
        self.results = [r.split('\a', 2) for r in result.strip().split('\n')]
        self.window.show_quick_panel(self.results, self.on_select)

    def on_select(self, selected):
        if 0 > selected < len(self.results):
            return
        item = self.results[selected]
        # the commit hash is the first thing on the second line
        # print(item[1].split(' ')[0])
        commit = item[1].split(' ')[0]
        ViewCollection.set_compare(commit)
        ViewCollection.add(self.view)

class GitGutterCompareBranch(sublime_plugin.WindowCommand):
    def run(self):
        self.view = self.window.active_view()
        key = ViewCollection.get_key(self.view)
        handler = ViewCollection.views[key]

        result = handler.git_branches().decode("utf-8")
        self.results = [self.parse_result(r) for r in result.strip().split('\n')]
        self.window.show_quick_panel(self.results, self.on_select)

    def parse_result(self, result):
        pieces = result.split('\a')
        message = pieces[0]
        branch  = pieces[1].split("/")[2]
        commit  = pieces[2][0:7]
        return [branch, commit + " " + message]

    def on_select(self, selected):
        if 0 > selected < len(self.results):
            return
        item = self.results[selected]
        # the commit hash is the first thing on the second line
        # print(item[1].split(' ')[0])
        commit = item[1].split(' ')[0]
        ViewCollection.set_compare(commit)
        ViewCollection.add(self.view)

class GitGutterCompareTag(sublime_plugin.WindowCommand):
    def run(self):
        self.view = self.window.active_view()
        key = ViewCollection.get_key(self.view)
        handler = ViewCollection.views[key]

        result = handler.git_tags().decode("utf-8")
        self.results = [self.parse_result(r) for r in result.strip().split('\n')]
        self.window.show_quick_panel(self.results, self.on_select)

    def parse_result(self, result):
        if not result:
            sublime.message_dialog("No tags found in repository")
            return
        pieces = result.split(' ')
        commit = pieces[0]
        tag    = pieces[1].replace("refs/tags/", "")
        return [tag, commit]

    def on_select(self, selected):
        if 0 > selected < len(self.results):
            return
        item = self.results[selected]
        commit = item[1]
        ViewCollection.set_compare(commit)
        ViewCollection.add(self.view)

class GitGutterCompareHead(sublime_plugin.WindowCommand):
    def run(self):
        self.view = self.window.active_view()
        ViewCollection.set_compare("HEAD")
        ViewCollection.add(self.view)

class GitGutterShowCompare(sublime_plugin.WindowCommand):
    def run(self):
        comparing = ViewCollection.get_compare()
        sublime.message_dialog("GitGutter is comparing against: " + comparing)

