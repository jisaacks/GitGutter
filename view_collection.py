import os
import sublime
import tempfile
import time

class ViewCollection:
    views = {} # Todo: these aren't really views but handlers. Refactor/Rename.
    git_times = {}
    git_files = {}
    buf_files = {}
    compare_against = "HEAD"

    @staticmethod
    def add(view):
        key = ViewCollection.get_key(view)
        try:
            from .git_gutter_handler import GitGutterHandler
        except (ImportError, ValueError):
            from git_gutter_handler import GitGutterHandler
        handler = ViewCollection.views[key] = GitGutterHandler(view)
        handler.reset()
        return handler

    @staticmethod
    def git_path(view):
        key = ViewCollection.get_key(view)
        if key in ViewCollection.views:
            return ViewCollection.views[key].get_git_path()
        else:
            return False

    @staticmethod
    def get_key(view):
        return view.file_name()

    @staticmethod
    def has_view(view):
        key = ViewCollection.get_key(view)
        return key in ViewCollection.views

    @staticmethod
    def get_handler(view):
        if ViewCollection.has_view(view):
            key = ViewCollection.get_key(view)
            return ViewCollection.views[key]
        else:
            return ViewCollection.add(view)

    @staticmethod
    def diff_line_change(view, line):
        return ViewCollection.get_handler(view).diff_line_change(line)

    @staticmethod
    def diff(view):
        return ViewCollection.get_handler(view).diff()

    @staticmethod
    def untracked(view):
        return ViewCollection.get_handler(view).untracked()

    @staticmethod
    def ignored(view):
        return ViewCollection.get_handler(view).ignored()

    @staticmethod
    def total_lines(view):
        return ViewCollection.get_handler(view).total_lines()

    @staticmethod
    def git_time(view):
        key = ViewCollection.get_key(view)
        if not key in ViewCollection.git_times:
            ViewCollection.git_times[key] = 0
        return time.time() - ViewCollection.git_times[key]

    @staticmethod
    def clear_git_time(view):
        key = ViewCollection.get_key(view)
        ViewCollection.git_times[key] = 0

    @staticmethod
    def update_git_time(view):
        key = ViewCollection.get_key(view)
        ViewCollection.git_times[key] = time.time()

    @staticmethod
    def tmp_file():
        '''
            Create a temp file and return the filepath to it.
            Caller is responsible for clean up
        '''
        fd, filepath = tempfile.mkstemp(prefix='git_gutter_')
        os.close(fd)
        return filepath

    @staticmethod
    def git_tmp_file(view):
        key = ViewCollection.get_key(view)
        if not key in ViewCollection.git_files:
            ViewCollection.git_files[key] = ViewCollection.tmp_file()
        return ViewCollection.git_files[key]

    @staticmethod
    def buf_tmp_file(view):
        key = ViewCollection.get_key(view)
        if not key in ViewCollection.buf_files:
            ViewCollection.buf_files[key] = ViewCollection.tmp_file()
        return ViewCollection.buf_files[key]

    @staticmethod
    def set_compare(commit):
        print("GitGutter now comparing against:",commit)
        ViewCollection.compare_against = commit

    @staticmethod
    def get_compare(view):
        compare = ViewCollection.compare_against or "HEAD"
        return view.settings().get('git_gutter_compare_against', compare)

    @staticmethod
    def current_branch(view):
        key = ViewCollection.get_key(view)
        return ViewCollection.views[key].git_current_branch()

    @staticmethod
    def show_status(view):
        key = ViewCollection.get_key(view)
        return ViewCollection.views[key].show_status


def plugin_loaded():
    settings = sublime.load_settings('GitGutter.sublime-settings')
    ViewCollection.compare_against = settings.get('compare_against', 'HEAD')
