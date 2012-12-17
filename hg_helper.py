import os


def hg_file_path(view, hg_path):
    if not hg_path:
        return False
    full_file_path = os.path.realpath(view.file_name())
    hg_path_to_file = full_file_path.replace(hg_path, '').replace('\\', '/')
    if hg_path_to_file[0] == '/':
        hg_path_to_file = hg_path_to_file[1:]
    return hg_path_to_file


def hg_root(directory):
    if os.path.exists(os.path.join(directory, '.hg')):
        return directory
    else:
        parent = os.path.realpath(os.path.join(directory, os.path.pardir))
        if parent == directory:
            # we have reached root dir
            return False
        else:
            return hg_root(parent)


def hg_tree(view):
    full_file_path = view.file_name()
    file_parent_dir = os.path.realpath(os.path.dirname(full_file_path))
    return hg_root(file_parent_dir)


def hg_dir(directory):
    if not directory:
        return False
    return os.path.join(directory, '.hg')
