import sublime

try:
    from .view_collection import ViewCollection
except (ImportError, ValueError):
    from view_collection import ViewCollection


class GitGutterCompareCommit():
    def __init__(self, view, git_handler):
        self.view = view
        self.git_handler = git_handler

    def run(self):
        self.results = self.commit_list()
        if self.results:
            self.view.window().show_quick_panel(self.results, self.on_select)

    def commit_list(self):
        result = self.git_handler.git_commits().decode("utf-8")
        return [r.split('\a', 2) for r in result.strip().split('\n')]

    def item_to_commit(self, item):
        return item[1].split(' ')[0]

    def on_select(self, selected):
        if 0 > selected < len(self.results):
            return
        item = self.results[selected]
        commit = self.item_to_commit(item)
        ViewCollection.set_compare(commit)
        self.git_handler.clear_git_time()
        self.git_handler.reset()


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
        ViewCollection.set_compare("HEAD")
        self.git_handler.clear_git_time()
        self.git_handler.reset()


class GitGutterCompareOrigin(GitGutterCompareCommit):
    def run(self):
        ViewCollection.set_compare("origin")
        self.git_handler.clear_git_time()
        self.git_handler.reset()


class GitGutterShowCompare(GitGutterCompareCommit):
    def run(self):
        comparing = ViewCollection.get_compare(self.view)
        sublime.message_dialog('GitGutter is comparing against: %s' % comparing)
