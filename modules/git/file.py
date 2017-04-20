# -*- coding: utf-8 -*-
import os
import tempfile
import zipfile

try:
    from io import BytesIO
except ImportError:
    from cStringIO import StringIO as BytesIO

# Comparing against HEAD
# 1. git status
# 3. git diff-index HEAD <file>

# Comparing against <commit>
# 1. git status  -> current branch, working file state
# 2. git diff-index <commit> <file>


class GitTreeObject(object):
    """The file within the git repository.

    Queried by:
        1) git diff-index -z 'HEAD'
        2) git archive --format=zip

    """
    def __init__(self, file_path):
        # case sensitive path to the file in the tree
        self.path = file_path
        # state of the file ('.', 'A', 'D', 'M', 'R')
        self.state = '.'
        # object id of the file in the tree
        self.tree_id = ''
        # object id of the file in the index (staging area)
        self.index_id = ''
        # content of the file read from git
        self.content = None
        # cache file on disk
        self.cache_file = None

    def __del__(self):
        """Delete temporary files."""
        if self.cache_file:
            os.unlink(self.cache_file)

    def parse_status(self, output):
        """Parse output of git diff-index -z"""
        if not output:
            self.state = '.'
            self.tree_id = ''
            self.index_id = ''
            self.content = None
            return
        # parse output
        # :\d{6} \d{6} \w+ \w+ [ADMR] path
        items = [item.decode() for item in output[1:].split(b'\x00')]
        _, _, self.tree_id, self.index_id, self.state, self.path = items

    def write_cache_file(self, output):
        """Write file from git to temporary cache file."""
        try:
            # Extract file content from zipped archive.
            # The `filelist` contains numerous directories finalized
            # by exactly one file whose content we are interested in.
            archive = zipfile.ZipFile(BytesIO(output))
            content = archive.read(archive.filelist[-1])
            # Mangle end of lines
            content = content.replace(b'\r\n', b'\n')
            content = content.replace(b'\r', b'\n')
            # Create temporary file
            if not self.cache_file:
                file, self.cache_file = tempfile.mkstemp(prefix='git_gutter_')
                os.close(file)
            # Write content to temporary file
            with open(self.cache_file, 'wb') as file:
                file.write(content)
        except Exception as error:
            print('GitGutter failed to create git cache: %s' % error)
