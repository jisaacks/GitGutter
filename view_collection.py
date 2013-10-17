import tempfile
import time


class ViewCollection:
    views = {}
    git_times = {}
    stg_times = {}
    git_files = {}
    buf_files = {}
    stg_files = {}

    @staticmethod
    def add(view):
        key = ViewCollection.get_key(view)
        try:
            from GitGutter.git_gutter_handler import GitGutterHandler
        except ImportError:
            from git_gutter_handler import GitGutterHandler
        ViewCollection.views[key] = GitGutterHandler(view)
        ViewCollection.views[key].reset()

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
