import os


def git_file_path(view, git_path):
    if not git_path:
        return False
    full_file_path = os.path.realpath(view.file_name())
    git_path_to_file = full_file_path.replace(git_path, '').replace('\\', '/')
    if git_path_to_file[0] == '/':
        git_path_to_file = git_path_to_file[1:]
    return git_path_to_file


def git_root(directory):
    if os.path.exists(os.path.join(directory, '.git')):
        return directory
    else:
        parent = os.path.realpath(os.path.join(directory, os.path.pardir))
        if parent == directory:
            # we have reached root dir
            return False
        else:
            return git_root(parent)


def git_tree(view):
    full_file_path = view.file_name()
    file_parent_dir = os.path.realpath(os.path.dirname(full_file_path))
    return git_root(file_parent_dir)


def git_dir(directory):
    if not directory:
        return False
    return os.path.join(directory, '.git')
