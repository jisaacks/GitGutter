import tempfile
import time


class ViewCollection:
    views = {} # Todo: these aren't really views but handlers. Refactor/Rename.
    git_times = {}
    stg_times = {}
    git_files = {}
    buf_files = {}
    stg_files = {}
    line_adjustment_map = {}
    compare_against = "HEAD"

    @staticmethod
    def add(view):
        key = ViewCollection.get_key(view)
        try:
            from GitGutter.git_gutter_handler import GitGutterHandler
        except ImportError:
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
    def diff(view):
        key = ViewCollection.get_key(view)
        return ViewCollection.views[key].diff()

    @staticmethod
    def has_stages(view):
        key = ViewCollection.get_key(view)
        return ViewCollection.views[key].has_stages()

    @staticmethod
    def staged(view):
        key = ViewCollection.get_key(view)
        return ViewCollection.views[key].staged()

    @staticmethod
    def unstaged(view):
        key = ViewCollection.get_key(view)
        return ViewCollection.views[key].unstaged()

    @staticmethod
    def untracked(view):
        key = ViewCollection.get_key(view)
        return ViewCollection.views[key].untracked()

    @staticmethod
    def ignored(view):
        key = ViewCollection.get_key(view)
        return ViewCollection.views[key].ignored()

    @staticmethod
    def total_lines(view):
        key = ViewCollection.get_key(view)
        return ViewCollection.views[key].total_lines()

    @staticmethod
    def git_time(view):
        key = ViewCollection.get_key(view)
        if not key in ViewCollection.git_times:
            ViewCollection.git_times[key] = 0
        return time.time() - ViewCollection.git_times[key]

    @staticmethod
    def clear_times(view):
        key = ViewCollection.get_key(view)
        ViewCollection.git_times[key] = 0
        ViewCollection.stg_times[key] = 0

    @staticmethod
    def update_git_time(view):
        key = ViewCollection.get_key(view)
        ViewCollection.git_times[key] = time.time()

    @staticmethod
    def stg_time(view):
        key = ViewCollection.get_key(view)
        if not key in ViewCollection.stg_times:
            ViewCollection.stg_times[key] = 0
        return time.time() - ViewCollection.stg_times[key]

    @staticmethod
    def update_stg_time(view):
        key = ViewCollection.get_key(view)
        ViewCollection.stg_times[key] = time.time()

    @staticmethod
    def git_tmp_file(view):
        key = ViewCollection.get_key(view)
        if not key in ViewCollection.git_files:
            ViewCollection.git_files[key] = tempfile.NamedTemporaryFile()
            ViewCollection.git_files[key].close()
        return ViewCollection.git_files[key]

    @staticmethod
    def buf_tmp_file(view):
        key = ViewCollection.get_key(view)
        if not key in ViewCollection.buf_files:
            ViewCollection.buf_files[key] = tempfile.NamedTemporaryFile()
            ViewCollection.buf_files[key].close()
        return ViewCollection.buf_files[key]

    @staticmethod
    def stg_tmp_file(view):
        key = ViewCollection.get_key(view)
        if not key in ViewCollection.stg_files:
            ViewCollection.stg_files[key] = tempfile.NamedTemporaryFile()
            ViewCollection.stg_files[key].close()
        return ViewCollection.stg_files[key]

    @staticmethod
    def set_compare(commit):
        print("GitGutter now comparing against:",commit)
        ViewCollection.compare_against = commit

    @staticmethod
    def get_compare():
        if ViewCollection.compare_against:
            return ViewCollection.compare_against
        else:
            return "HEAD"

    @staticmethod
    def set_line_adjustment_map(view, adj_map):
        key = ViewCollection.get_key(view)
        ViewCollection.line_adjustment_map[key] = adj_map

    def get_line_adjustment_map(view):
        key = ViewCollection.get_key(view)
        if key in ViewCollection.line_adjustment_map:
            return ViewCollection.line_adjustment_map[key]
        else:
            # Zero adjustments
            return {0:0}
