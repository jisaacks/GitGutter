import os.path

try:
    from nt import _getfinalpathname
    def realpath(path):
        """Resolve symlinks and return real path to file.

        Note:
            This is a fix for the issue of os.path.realpath() not to resolve
            symlinks on Windows as it is an alias to abspath() only.
            see: http://bugs.python.org/issue9949

        Arguments:
            path (string): The path to resolve.

        Returns:
            string: The resolved absolute path if exists or path as provided
                otherwise.
        """
        try:
            return _getfinalpathname(
                path).replace('\\\\?\\', '') if path else None
        except FileNotFoundError:
            return path

except (AttributeError, ImportError):
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
        This is a local alternitive to calling the git command:

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
