# -*- coding: utf-8 -*-
import sublime


def set_against_commit(git_gutter, **kwargs):
    """Show a quick panel with commits to be chosen from as compare against.

    Arguments:
        git_gutter (GitGutterCommand): The main command object, which
            represents GitGutter.
        kwargs (dict): The arguments received from the `run_command`.
            This argument is declared to create a common interface being used
            by the GitGutterCommand object.
    """
    def show_quick_panel(output):
        """Parse git output and present the quick panel.

        Arguments:
            output (string): The output of git with the list of commits.
        """
        if not output:
            return sublime.message_dialog('No commits found in repository.')

        # Create the list of commits to show in the quick panel
        items = [r.split('\a') for r in output.split('\n')]

        def on_done(index):
            """Select new compare target according to user selection."""
            if index > -1:
                git_gutter.git_handler.set_compare_against(
                    items[index][0].split(' ')[0])

        git_gutter.view.window().show_quick_panel(items, on_done)

    git_gutter.git_handler.git_commits().then(show_quick_panel)


def set_against_file_commit(git_gutter, **kwargs):
    """Show a quick panel with commits to be chosen from as compare against.

    Arguments:
        git_gutter (GitGutterCommand): The main command object, which
            represents GitGutter.
        kwargs (dict): The arguments received from the `run_command`.
            This argument is declared to create a common interface being used
            by the GitGutterCommand object.
    """
    def show_quick_panel(output):
        """Parse git output and present the quick panel.

        Arguments:
            output (string): The output of git with the list of commits.
        """
        if not output:
            return sublime.message_dialog(
                'No commits of this file found in repository.')

        # Sort items by author date in reversed order,
        # split each line by \a and strip time stamp from beginning
        items = [
            r.split('\a')[1:] for r in sorted(output.split('\n'), reverse=True)
        ]

        def on_done(index):
            """Select new compare target according to user selection."""
            if index > -1:
                git_gutter.git_handler.set_compare_against(
                    items[index][0].split(' ')[0])

        git_gutter.view.window().show_quick_panel(items, on_done)

    git_gutter.git_handler.git_file_commits().then(show_quick_panel)


def set_against_branch(git_gutter, **kwargs):
    """Show a quick panel with branches to be chosen from as compare against.

    Arguments:
        git_gutter (GitGutterCommand): The main command object, which
            represents GitGutter.
        kwargs (dict): The arguments received from the `run_command`.
            This argument is declared to create a common interface being used
            by the GitGutterCommand object.
    """
    def show_quick_panel(output):
        """Parse git output and present the quick panel.

        Arguments:
            output (string): The output of git with the list of branches.
        """
        if not output:
            return sublime.message_dialog('No branches found in repository.')

        def parse_result(result):
            """Create a quick panel item for one line of git's output."""
            branch, commit, name, date = result.split('\a')
            branch = branch[11:]   # skip 'refs/heads/'
            return [branch, commit, name, date]

        # Create the list of branches to show in the quick panel
        items = [parse_result(r) for r in output.split('\n')]

        def on_done(index):
            """Select new compare target according to user selection."""
            if index > -1:
                git_gutter.git_handler.set_compare_against(
                    'refs/heads/%s' % items[index][0])

        git_gutter.view.window().show_quick_panel(items, on_done)

    git_gutter.git_handler.git_branches().then(show_quick_panel)


def set_against_tag(git_gutter, **kwargs):
    """Show a quick panel with tags to be chosen from as compare against.

    Arguments:
        git_gutter (GitGutterCommand): The main command object, which
            represents GitGutter.
        kwargs (dict): The arguments received from the `run_command`.
            This argument is declared to create a common interface being used
            by the GitGutterCommand object.
    """
    def show_quick_panel(output):
        """Parse git output and present the quick panel.

        Arguments:
            output (string): The output of git with the list of tags.
        """
        if not output:
            return sublime.message_dialog('No tags found in repository.')

        def parse_result(result):
            """Create a quick panel item for one line of git's output."""
            tag, commit, tname, tdate, cname, cdate = result.split('\a')
            tag = tag[10:]         # skip 'refs/heads/'
            return [tag, commit, tname.strip() or cname, tdate.strip() or cdate]

        # Create the list of tags to show in the quick panel
        items = [parse_result(r) for r in output.split('\n')]

        def on_done(index):
            """Select new compare target according to user selection."""
            if index > -1:
                git_gutter.git_handler.set_compare_against(
                    'refs/tags/%s' % items[index][0])

        git_gutter.view.window().show_quick_panel(items, on_done)

    git_gutter.git_handler.git_tags().then(show_quick_panel)


def set_against_head(git_gutter, **kwargs):
    """Set HEAD as compare target.

    Arguments:
        git_gutter (GitGutterCommand): The main command object, which
            represents GitGutter.
        kwargs (dict): The arguments received from the `run_command`.
            This argument is declared to create a common interface being used
            by the GitGutterCommand object.
    """
    git_gutter.git_handler.set_compare_against('HEAD', True)


def set_against_origin(git_gutter, **kwargs):
    """Set origin as compare target.

    Arguments:
        git_gutter (GitGutterCommand): The main command object, which
            represents GitGutter.
        kwargs (dict): The arguments received from the `run_command`.
            This argument is declared to create a common interface being used
            by the GitGutterCommand object.
    """
    def on_branch_name(status):
        if not status or not status.get('remote'):
            sublime.message_dialog('Current branch has not tracking remote!')
        git_gutter.git_handler.set_compare_against(status.get('remote'), True)

    git_gutter.git_handler.git_branch_status().then(on_branch_name)


def show_compare(git_gutter, **kwargs):
    """Show a dialog to display current compare target.

    Arguments:
        git_gutter (GitGutterCommand): The main command object, which
            represents GitGutter.
        kwargs (dict): The arguments received from the `run_command`.
            This argument is declared to create a common interface being used
            by the GitGutterCommand object.
    """
    comparing = git_gutter.git_handler.format_compare_against()
    sublime.message_dialog(
        'GitGutter is comparing against: %s' % comparing)
