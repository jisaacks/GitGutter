import tempfile
import time

from vcs_helpers import GitHelper
from vcs_helpers import HgHelper
from vcs_helpers import SvnHelper


class ViewCollection:
    views = {}
    vcs_times = {}
    vcs_files = {}
    buf_files = {}

    @staticmethod
    def add(view):
        from gutter_handlers import GitGutterHandler
        from gutter_handlers import HgGutterHandler
        from gutter_handlers import SvnGutterHandler
        handler = None
        if GitHelper.is_git_repository(view):
            handler = GitGutterHandler(view)
        elif HgHelper.is_hg_repository(view):
            handler = HgGutterHandler(view)
        elif SvnHelper.is_svn_repository(view):
            handler = SvnGutterHandler(view)

        # If no handler found then either the view does not represent a
        # file on disk (e.g. not yet saved) or the file is not in a supported
        # VCS repository.
        if handler is not None:
            key = ViewCollection.get_key(view)
            ViewCollection.views[key] = handler
            ViewCollection.views[key].reset()

    @staticmethod
    def vcs_path(view):
        key = ViewCollection.get_key(view)
        if key in ViewCollection.views:
            return ViewCollection.views[key].get_vcs_path()
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
    def vcs_time(view):
        key = ViewCollection.get_key(view)
        if not key in ViewCollection.vcs_times:
            ViewCollection.vcs_times[key] = 0
        return time.time() - ViewCollection.vcs_times[key]

    @staticmethod
    def update_vcs_time(view):
        key = ViewCollection.get_key(view)
        ViewCollection.vcs_times[key] = time.time()

    @staticmethod
    def vcs_tmp_file(view):
        key = ViewCollection.get_key(view)
        if not key in ViewCollection.vcs_files:
            ViewCollection.vcs_files[key] = tempfile.NamedTemporaryFile()
            ViewCollection.vcs_files[key].close()
        return ViewCollection.vcs_files[key]

    @staticmethod
    def buf_tmp_file(view):
        key = ViewCollection.get_key(view)
        if not key in ViewCollection.buf_files:
            ViewCollection.buf_files[key] = tempfile.NamedTemporaryFile()
            ViewCollection.buf_files[key].close()
        return ViewCollection.buf_files[key]
