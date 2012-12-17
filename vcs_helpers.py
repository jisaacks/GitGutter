import os


class VcsHelper(object):
    @classmethod
    def vcs_dir(cls, directory):
        """Return the path to the metadata directory, assuming it is
        directly under the passed directory."""
        if not directory:
            return False
        return os.path.join(directory, cls.meta_data_directory())

    @classmethod
    def vcs_file_path(cls, view, vcs_path):
        """Returns the relative path to the file in the Sublime view, in
        the repository rooted at vcs_path."""
        if not vcs_path:
            return False
        full_file_path = os.path.realpath(view.file_name())
        vcs_path_to_file = \
            full_file_path.replace(vcs_path, '').replace('\\', '/')
        if vcs_path_to_file[0] == '/':
            vcs_path_to_file = vcs_path_to_file[1:]
        return vcs_path_to_file

    @classmethod
    def vcs_root(cls, directory):
        """Returns the top-level directory of the repository."""
        if os.path.exists(os.path.join(directory,
            cls.meta_data_directory())):
            return directory
        else:
            parent = os.path.realpath(os.path.join(directory, os.path.pardir))
            if parent == directory:
                # we have reached root dir
                return False
            else:
                return cls.vcs_root(parent)

    @classmethod
    def vcs_tree(cls, view):
        """Returns the directory at the top of the tree that contains
        the file in the passed Sublime view."""
        full_file_path = view.file_name()
        file_parent_dir = os.path.realpath(os.path.dirname(full_file_path))
        return cls.vcs_root(file_parent_dir)


class GitHelper(VcsHelper):
    @classmethod
    def meta_data_directory(cls):
        return '.git'


class HgHelper(VcsHelper):
    @classmethod
    def meta_data_directory(cls):
        return '.hg'
