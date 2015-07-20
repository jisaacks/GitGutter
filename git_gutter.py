import os
import sublime
import sublime_plugin
try:
    from .git_gutter_handler import GitGutterHandler
    from .git_gutter_settings import GitGutterSettings
    from .git_gutter_compare import GitGutterCompareCommit, GitGutterCompareBranch, GitGutterCompareTag, GitGutterCompareHead, GitGutterCompareOrigin
    from .git_gutter_jump_to_changes import GitGutterJumpToChanges
    from .git_gutter_show_diff import GitGutterShowDiff
except (ImportError, ValueError):
    from git_gutter_handler import GitGutterHandler
    from git_gutter_settings import GitGutterSettings
    from git_gutter_compare import GitGutterCompareCommit, GitGutterCompareBranch, GitGutterCompareTag, GitGutterCompareHead, GitGutterCompareOrigin
    from git_gutter_jump_to_changes import GitGutterJumpToChanges
    from git_gutter_show_diff import GitGutterShowDiff

class GitGutterCommand(sublime_plugin.TextCommand):
    region_names = ['deleted_top', 'deleted_bottom',
                    'deleted_dual', 'inserted', 'changed',
                    'untracked', 'ignored']

    def __init__(self, *args, **kwargs):
        sublime_plugin.TextCommand.__init__(self, *args, **kwargs)
        self.git_handler = GitGutterHandler(self.view)
        self.show_diff_handler = GitGutterShowDiff(self.view, self.git_handler)

    def run(self, edit_permit, **kwargs):
        if self.git_handler.on_disk() is False:
            return

        if kwargs and 'action' in kwargs:
            action = kwargs['action']
            if action == 'jump_to_next_change':
                GitGutterJumpToChanges(self.view, self.git_handler).jump_to_next_change()
            elif action == 'jump_to_prev_change':
                GitGutterJumpToChanges(self.view, self.git_handler).jump_to_prev_change()
            elif action == 'show_compare':
                sublime.message_dialog("GitGutter is comparing against: " + GitGutterSettings.compare_against())
            elif action == 'compare_against_commit':
                GitGutterCompareCommit(self.view, self.git_handler).run()
            elif action == 'compare_against_branch':
                GitGutterCompareBranch(self.view, self.git_handler).run()
            elif action == 'compare_against_tag':
                GitGutterCompareTag(self.view, self.git_handler).run()
            elif action == 'compare_against_head':
                GitGutterCompareHead(self.view, self.git_handler).run()
            elif action == 'compare_against_origin':
                GitGutterCompareOrigin(self.view, self.git_handler).run()
        else:
            self.show_diff_handler.run()
