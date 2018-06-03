# -*- coding: utf-8 -*-
import os.path

try:
    from nt import _getfinalpathname
    from sys import getwindowsversion
    assert getwindowsversion().major >= 6

    def realpath(path):
        """Resolve symlinks and return real path to file.

        Note:
            This is a fix for the issue of `os.path.realpath()` not to resolve
            symlinks on Windows as it is an alias to `os.path.abspath()` only.
            see: http://bugs.python.org/issue9949

            This fix applies to local paths only as symlinks are not resolved
            by _getfinalpathname on network drives anyway.

            Also note that _getfinalpathname in Python 3.3 throws
            `NotImplementedError` on Windows versions prior to Windows Vista,
            hence we fallback to `os.path.abspath()` on these platforms.

        Arguments:
            path (string): The path to resolve.

        Returns:
            string: The resolved absolute path if exists or path as provided
                otherwise.
        """
        try:
            if path:
                real_path = _getfinalpathname(path)
                if real_path[5] == ':':
                    # Remove \\?\ from beginning of resolved path
                    return real_path[4:]
                return os.path.abspath(path)
        except FileNotFoundError:
            pass
        return path

except (AttributeError, ImportError, AssertionError):
    def realpath(path):
        """Resolve symlinks and return real path to file.

        Arguments:
            path (string): The path to resolve.

        Returns:
            string: The resolved absolute path.
        """
        return os.path.realpath(path) if path else None


def is_work_tree(path):
    """Check if 'path' is a valid git working tree.

    A working tree contains a `.git` directory or file.

    Arguments:
        path (string): The path to check.

    Returns:
        bool: True if path contains a '.git'
    """
    return path and os.path.exists(os.path.join(path, '.git'))


def split_work_tree(file_path):
    """Split the 'file_path' into working tree and relative path.

    The file_path is converted to a absolute real path and split into
    the working tree part and relative path part.

    Note:
        This is a local alternative to calling the git command:

            git rev-parse --show-toplevel

    Arguments:
        file_path (string): Absolute path to a file.

    Returns:
        A tuple of two the elements (working tree, file path).
    """
    if file_path:
        path, name = os.path.split(file_path)
        # files within '.git' path are not part of a work tree
        while path and name and name != '.git':
            if is_work_tree(path):
                return (path, os.path.relpath(
                    file_path, path).replace('\\', '/'))
            path, name = os.path.split(path)
    return (None, None)


def translate_to_wsl(path):
    """Translate a windows path to unix path for WSL.

    WSL stands for Windows Subsystem for Linux and allows to run native linux
    programs on Windows. In order to access Windows' filesystem the local
    drives are mounted to /mnt/<Drive> within the WSL shell. This little helper
    function translates a windows path to such a WSL compatible path.

    Note:
        This function works for local files only at the moment.

    Arguments:
        path (string): the windows path to translate to unix path

    Returns:
        string: the unix path to be used by calls to programs running on WSL

    Raises:
        FileNotFoundError: if path is an UNC path.
    """
    if path.startswith('\\\\'):
        raise FileNotFoundError('UNC paths are not supported by WSL!')
    wsl_path = path.replace('\\', '/')
    if wsl_path[1:3] == ':/':
        return ''.join(('/mnt/', wsl_path[0].lower(), wsl_path[2:]))
    return wsl_path
