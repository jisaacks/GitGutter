import os
import tempfile

# The folder to place all temporary files into.
TEMP_DIR = os.path.join(tempfile.gettempdir(), "GitGutter")


class TempFile(object):
    """A temporary file object which allows shared reading.

    All the temporary files created by the `tempfile` module's functions are
    accessible by the calling process only on some operating systems.
    Therefore this class represents a file which is deleted as soon as the
    object is destroyed but without keeping the file open all the time.
    """

    def __init__(self, mode='r'):
        """Initialize TempFile object."""
        try:
            os.mkdir(TEMP_DIR)
        except FileExistsError:
            pass
        self.name = tempfile.mktemp(dir=TEMP_DIR)
        self._mode = mode
        self._file = None
        # Cache unlink to keep it available even though the 'os' module is
        # already None'd out whenever __del__() is called.
        # See python stdlib's tempfile.py for details.
        self._unlink = os.unlink

    def __del__(self):
        """Destroy the TempFile object and remove the file from disk."""
        self.close()
        try:
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
