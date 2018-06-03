# -*- coding: utf-8 -*-
import errno
import os
import tempfile
import time

# The folder to place all temporary files into.
TEMP_DIR = os.environ.get('XDG_RUNTIME_DIR')
if TEMP_DIR:
    # If available use the per user XDS_RUNTIME_DIR on unix based OSs.
    TEMP_DIR = os.path.join(TEMP_DIR, 'GitGutter')
else:
    # Otherwise fallback to the default TEMP folder.
    TEMP_DIR = os.path.join(tempfile.gettempdir(), 'GitGutter')
    if hasattr(os, 'getuid'):
        TEMP_DIR += '.%s' % os.getuid()


def plugin_loaded():
    """Sublime Text plugin loaded callback.

    Remove all temporary files older than 2 days. Looks like in some cases some
    temporary files are not deleted, if ST is closed. So try to delete too old
    ones upon startup. Wait 2 days to reduce the chance of deleting temporary
    files of another open ST instance.
    """
    now = time.time()
    max_age = 48 * 60 * 60
    try:
        files = os.listdir(TEMP_DIR)
    except FileNotFoundError:
        # tempfolder does not exist
        pass
    else:
        for name in files:
            try:
                path = os.path.join(TEMP_DIR, name)
                if now - os.path.getatime(path) > max_age:
                        os.remove(path)
            except OSError:
                pass


class TempFile(object):
    """A temporary file object which allows shared reading.

    All the temporary files created by the `tempfile` module's functions are
    accessible by the calling process only on some operating systems.
    Therefore this class represents a file which is deleted as soon as the
    object is destroyed but without keeping the file open all the time.
    """

    def __init__(self, mode='r'):
        """Initialize TempFile object."""
        self.name = tempfile.mktemp(dir=TEMP_DIR)
        self._file = None
        self._mode = mode
        # Cache unlink to keep it available even though the 'os' module is
        # already None'd out whenever __del__() is called.
        # See python stdlib's tempfile.py for details.
        self._unlink = os.unlink

        try:
            # ensure cache directory exists with write permissions
            os.makedirs(TEMP_DIR, 0o700)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    def __del__(self):
        """Destroy the TempFile object and remove the file from disk."""
        try:
            self.close()
            self._unlink(self.name)
        except OSError:
            pass

    def __enter__(self):
        """`With` statement support."""
        return self.open()

    def __exit__(self, exc, value, tb):
        """`With` statement support."""
        self.close()

    def open(self):
        """Open temporary file."""
        if self._file is None:
            self._file = open(self.name, mode=self._mode)
        return self._file

    def close(self):
        """Close temporary file."""
        if self._file is not None:
            self._file.close()
            self._file = None

    def tell(self):
        return self._file.tell()
