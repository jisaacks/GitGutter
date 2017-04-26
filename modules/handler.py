# -*- coding: utf-8 -*-
import codecs
import functools
import os
import re
import subprocess
import tempfile
import zipfile

try:
    from io import BytesIO
except ImportError:
    from cStringIO import StringIO as BytesIO

try:
    from subprocess import TimeoutExpired
    _HAVE_TIMEOUT = True
except ImportError:
    class TimeoutExpired(Exception):
        pass
    _HAVE_TIMEOUT = False

import sublime

from . import path
from .promise import Promise

# The view class has a method called 'change_count()'
_HAVE_VIEW_CHANGE_COUNT = hasattr(sublime.View, "change_count")

try:
    set_timeout = sublime.set_timeout_async
except AttributeError:
    set_timeout = sublime.set_timeout


class GitGutterHandler(object):

    # The working tree / compare target map as class wide attribute.
    # It is initialized once and keeps the values of all object instantces.
    _compare_against_mapping = {}

    def __init__(self, view, settings):
        """Initialize GitGutterHandler object."""
        self.settings = settings
        # attached view being tracked
        self.view = view
        # cached view file name to detect renames
        self._view_file_name = None
        # path to temporary file with view content
        self._view_temp_file = None
        # last view change count
        self._view_change_count = -1
        # path to temporary file with git index content
        self._git_temp_file = None
        # temporary file contains up to date information
        self._git_temp_file_valid = False
        # real path to current work tree
        self._git_tree = None
        # relative file path in work tree
        self._git_path = None
        # cached branch name
        self._git_branch = None
        # file is part of the git repository
        self.git_tracked = False
        # compare target commit hash
        self._git_compared_commit = None
        # cached git diff result for diff popup
        self._git_diff_cache = ''

    def __del__(self):
        """Delete temporary files."""
        if self._git_temp_file:
            os.unlink(self._git_temp_file)
        if self._view_temp_file:
            os.unlink(self._view_temp_file)

    @staticmethod
    def tmp_file():
        """Create a temp file and return the filepath to it.

        CAUTION: Caller is responsible for clean up
        """
        file, filepath = tempfile.mkstemp(prefix='git_gutter_')
        os.close(file)
        return filepath

    @property
    def repository_name(self):
        """Return the folder name of the working tree as repository name."""
        return os.path.basename(
            self._git_tree) if self._git_tree else '(None)'

    def work_tree(self, validate=False):
        """Return the real path of a valid work-tree or None.

        Arguments:
            validate (bool): If True check whether the file is part of a valid
                             git repository or return the cached working tree
                             path only on False.
        """
        if validate:
            # Check if file exists
            file_name = path.realpath(self.view.file_name())
            if not file_name or not os.path.isfile(file_name):
                self._view_file_name = None
                self._git_tree = None
                self._git_path = None
                return None
            # Check if file was renamed
            is_renamed = file_name != self._view_file_name
            if is_renamed or not path.is_work_tree(self._git_tree):
                self._view_file_name = file_name
                self._git_tree, self._git_path = path.split_work_tree(file_name)
                self.invalidate_git_file()
        return self._git_tree

    def get_compare_against(self):
        """Return the compare target for a view.

        If interactivly specified a compare target for the view's repository,
        use it first, then try view's settings, which includes project
        settings and preferences. Finally try GitGutter.sublime-settings or
        fall back to HEAD if everything goes wrong to avoid exceptions.

        Returns:
            string: HEAD/branch/tag/remote/commit
                The reference to compare the view against.
        """
        # Interactively specified compare target overrides settings.
        if self._git_tree in self._compare_against_mapping:
            return self._compare_against_mapping[self._git_tree]
        # Project settings and Preferences override plugin settings if set.
        return self.settings.get('compare_against', 'HEAD')

    def set_compare_against(self, compare_against, refresh=False):
        """Apply a new branch/commit/tag string the view is compared to.

        If one of the settings 'focus_change_mode' or 'live_mode' is true,
        the view, is automatically compared by 'on_activate' event when
        returning from a quick panel and therefore the command 'git_gutter'
        can be omitted. This assumption can be overridden by 'refresh' for
        commands that do not show a quick panel.

        Arguments:
            compare_against (string): The branch, commit or tag as returned
                from 'git show-ref' to compare the view against
            refresh (bool): True to force git diff and update GUI
        """
        self._compare_against_mapping[self._git_tree] = compare_against
        # force refresh if live_mode and focus_change_mode are disabled
        refresh |= (not self.settings.get('live_mode') and
                    not self.settings.get('focus_change_mode'))
        # set view id to ommit from evaluation
        active_view_id = 0 if refresh else self.view.id()
        # refresh all visible views
        for window in sublime.windows():
            for group in range(window.num_groups()):
                view = window.active_view_in_group(group)
                if view and view.id() != active_view_id:
                    view.run_command('git_gutter')

    def format_compare_against(self):
        """Format the compare against setting to use for display."""
        comparing = self.get_compare_against()
        for repl in ('refs/heads/', 'refs/remotes/', 'refs/tags/'):
            comparing = comparing.replace(repl, '')
        return comparing

    def _get_view_encoding(self):
        """Read view encoding and transform it for use with python.

        This method reads `origin_encoding` used by ConvertToUTF8 plugin and
        goes on with ST's encoding setting if required. The encoding is
        transformed to work with python's `codecs` module.

        Returns:
            string: python compatible view encoding
        """
        encoding = self.view.settings().get('origin_encoding')
        if not encoding:
            encoding = self.view.encoding()
            if encoding == "Undefined":
                encoding = self.view.settings().get('default_encoding')
            begin = encoding.find('(')
            if begin > -1:
                encoding = encoding[begin + 1:-1]
            encoding = encoding.replace('with BOM', '')
            encoding = encoding.replace('Windows', 'cp')
            encoding = encoding.replace('-', '_')
        encoding = encoding.replace(' ', '')
        return encoding

    def in_repo(self):
        """Return true, if the most recent `git show` returned any content.

        If `git show` returns empty content, any diff will result in
        all lines added state and the view's file is most commonly untracked.
        """
        return self.git_tracked

    def invalidate_view_file(self):
        """Reset change_count and force writing the view cache file.

        The view content is written to a temporary file for use with git diff,
        if the view.change_count() has changed. This method forces the update
        on the next call of update_view_file().
        """
        self._view_change_count = -1

    def update_view_file(self):
        """Write view's content to a temporary file as source for git diff.

        The file is updated only if the view.change_count() has changed to
        reduce the number of required disk writes.

        Returns:
            bool: True indicates updated file.
                  False is returned if file is up to date.
        """
        change_count = 0
        if _HAVE_VIEW_CHANGE_COUNT:
            # write view buffer to file only, if changed
            change_count = self.view.change_count()
            if self._view_change_count == change_count:
                return False
        # Read from view buffer
        chars = self.view.size()
        region = sublime.Region(0, chars)
        contents = self.view.substr(region)
        # Try conversion
        try:
            encoding = self._get_view_encoding()
            encoded = contents.encode(encoding)
        except (LookupError, UnicodeError):
            # Fallback to utf8-encoding
            encoded = contents.encode('utf-8')
        try:
            # Write the encoded content to file
            if not self._view_temp_file:
                self._view_temp_file = self.tmp_file()
            with open(self._view_temp_file, 'wb') as file:
                if self.view.encoding() == "UTF-8 with BOM":
                    file.write(codecs.BOM_UTF8)
                file.write(encoded)
        except OSError as error:
            print('GitGutter failed to create view cache: %s' % error)
            return False
        # Update internal change counter after job is done
        self._view_change_count = change_count
        return True

    def is_git_file_valid(self):
        """Return True if temporary file is marked up to date."""
        return self._git_temp_file_valid

    def invalidate_git_file(self):
        """Invalidate all cached results of recent git commands."""
        self._git_temp_file_valid = False
        # cached branch name
        self._git_branch = None

    def update_git_file(self):
        """Update file from git index and write it to a temporary file.

        Query the compare target's object id from git, if the compare target
        is not a specific hash already. Then read the file from git index only,
        if the commit has changed since last call. If the commit is still the
        same the file did not change, too and reading it would waste resources.

        Returns:
            Promise resolved with True if the temporary file was updated.
        """
        # Always resolve with False if temporary file is marked up to date.
        if self._git_temp_file_valid:
            return Promise.resolve(False)
        self._git_temp_file_valid = True

        # Read commit hash from git if compare target is a reference.
        refs = self.get_compare_against()
        if 'HEAD' in refs or '/' in refs:
            return self.git_compare_commit(refs).then(self._update_from_commit)
        return self._update_from_commit(refs)

    def _update_from_commit(self, compared_id):
        """Update git file from commit, if the commit id changed.

        The compared_id is compared to the last compare target. If it changed,
        the temporary git file is updated from the provided commit.

        Arguments:
            compared_id (string): Full hash of the commit the view is currently
                compared against.

        Returns:
            bool: True if temporary file was updated, False otherwise.
        """
        if self._git_compared_commit == compared_id:
            return Promise.resolve(False)
        return self.git_read_file(compared_id).then(
            functools.partial(self._write_git_file, compared_id))

    def _write_git_file(self, compared_id, contents):
        """Extract output and write it to a temporary file.

        The function resolves the promise with True to indicate the
        updated git file.

        Arguments:
            compared_id (string): The new compare target's object id to store.
            contents (string): The file contents read from git.

        Returns:
            bool: True if file was written to disc successfully.
        """
        try:
            # Mangle end of lines
            contents = contents.replace(b'\r\n', b'\n')
            contents = contents.replace(b'\r', b'\n')
            # Create temporary file
            if not self._git_temp_file:
                self._git_temp_file = self.tmp_file()
            # Write content to temporary file
            with open(self._git_temp_file, 'wb') as file:
                file.write(contents)
            # Indicate success.
            self._git_compared_commit = compared_id
            self.git_tracked = True
            return True
        except AttributeError:
            # Git returned empty output, file is not tracked
            self._git_compared_commit = compared_id
            self.git_tracked = False
            return False
        except OSError as error:
            print('GitGutter failed to create git cache: %s' % error)
            return False

    def diff(self):
        """Run git diff to check for inserted, modified and deleted lines.

        Returns:
            Promise: The Promise object containing the processed git diff.
        """
        return self.update_git_file().then(self._run_diff)

    def _run_diff(self, updated_git_file):
        """Call git diff and return the decoded unified diff string.

        Arguments:
            updated_git_file (bool): Is True if the file was updated
                from git database since last call.
        Returns:
            tuple: (first_line, last_line, [inserted], [modified], [deleted])
                The processed result of git diff with the information about
                the modifications of the file.
            None: Returns None if nothing has changed since last call.
        """
        updated_view_file = self.update_view_file()
        if not updated_git_file and not updated_view_file:
            return self.process_diff(self._git_diff_cache)

        args = list(filter(None, (
            self.settings.git_binary,
            'diff', '-U0', '--no-color', '--no-index',
            self.settings.ignore_whitespace,
            self.settings.patience_switch,
            self._git_temp_file,
            self._view_temp_file,
        )))
        return self.execute_async(
            args=args, decode=False).then(self._decode_diff)

    def _decode_diff(self, results):
        encoding = self._get_view_encoding()
        try:
            decoded_results = results.decode(encoding)
        except AttributeError:
            # git returned None on stdout
            decoded_results = ''
        except UnicodeError:
            try:
                decoded_results = results.decode('utf-8')
            except UnicodeDecodeError:
                decoded_results = ''
        except LookupError:
            try:
                decoded_results = codecs.decode(results)
            except UnicodeDecodeError:
                decoded_results = ''
        # cache the diff result for reuse with diff_popup.
        self._git_diff_cache = decoded_results
        return self.process_diff(decoded_results)

    @staticmethod
    def process_diff(diff_str):
        r"""Parse unified diff with 0 lines of context.

        Hunk range info format:
          @@ -3,2 +4,0 @@
            Hunk originally starting at line 3, and occupying 2 lines, now
            starts at line 4, and occupies 0 lines, i.e. it was deleted.
          @@ -9 +10,2 @@
            Hunk size can be omitted, and defaults to one line.

        Dealing with ambiguous hunks:
          "A\nB\n" -> "C\n"
          Was 'A' modified, and 'B' deleted? Or 'B' modified, 'A' deleted?
          Or both deleted? To minimize confusion, let's simply mark the
          hunk as modified.

        Arguments:
            diff_str (string): The unified diff string to parse.

        Returns:
            tuple: (first, last, [inserted], [modified], [deleted])
                A tuple with meta information of the diff result.
        """
        # first and last changed line in the view
        first, last = 0, 0
        # lists with inserted, modified and deleted lines
        inserted, modified, deleted = [], [], []
        hunk_re = r'^@@ \-(\d+),?(\d*) \+(\d+),?(\d*) @@'
        for hunk in re.finditer(hunk_re, diff_str, re.MULTILINE):
            _, old_size, start, new_size = hunk.groups()
            start = int(start)
            old_size = int(old_size or 1)
            new_size = int(new_size or 1)
            if first == 0:
                first = max(1, start)
            if not old_size:
                last = start + new_size
                inserted += range(start, last)
            elif not new_size:
                last = start + 1
                deleted.append(last)
            else:
                last = start + new_size
                modified += range(start, last)
        return (first, last, inserted, modified, deleted)

    def diff_changed_blocks(self):
        """Create a list of all changed code blocks from cached diff result.

        Returns:
            list: A list with the row numbers of all changed code blocks.
        """
        hunk_re = r'^@@ \-\d+,?\d* \+(\d+),?\d* @@'
        hunks = re.finditer(hunk_re, self._git_diff_cache, re.MULTILINE)
        return [int(hunk.group(1)) for hunk in hunks]

    def diff_line_change(self, row):
        """Use cached diff result to extract the changes of a certain line.

        Arguments:
            row (int): The row to find the changes for

        Returns:
            tuple: The tuple contains 4 items of information about changes
                around the row with (deleted_lines, start, size, meta).
        """
        hunk_re = r'^@@ \-(\d+),?(\d*) \+(\d+),?(\d*) @@'
        hunks = re.finditer(hunk_re, self._git_diff_cache, re.MULTILINE)
        # if wrap is disable avoid wrapping
        wrap = self.settings.get('next_prev_change_wrap')
        # we also want to extract the position of the surrounding changes
        first_change = prev_change = next_change = None

        for hunk in hunks:
            _, _, start, size = hunk.groups()
            start = int(start)
            size = int(size or 1)
            if first_change is None:
                first_change = start
            # special handling to also match the line below deleted
            # content
            if size == 0 and row == start + 1:
                pass
            # continue if the hunk is before the line
            elif start + size < row:
                prev_change = start
                continue
            # break if the hunk is after the line
            elif row < start:
                break
            # in the following the line is inside the hunk
            try:
                next_hunk = next(hunks)
                hunk_end = next_hunk.start()
                next_change = int(next_hunk.group(3))
            except:
                hunk_end = len(self._git_diff_cache)

            if not wrap:
                if prev_change is None:
                    prev_change = start
                if next_change is None:
                    next_change = start

            # if prev change is None set it to the wrap around the
            # document: prev -> last hunk, next -> first hunk
            if prev_change is None:
                try:
                    remaining_hunks = list(hunks)
                    if remaining_hunks:
                        last_hunk = remaining_hunks[-1]
                        prev_change = int(last_hunk.group(3))
                    elif next_change is not None:
                        prev_change = next_change
                    else:
                        prev_change = start
                except:
                    prev_change = start
            if next_change is None:
                next_change = first_change

            # extract the content of the hunk
            hunk_content = self._git_diff_cache[hunk.start():hunk_end]
            # store all deleted lines (starting with -)
            hunk_lines = hunk_content.splitlines()[1:]
            deleted_lines = [
                line[1:] for line in hunk_lines if line.startswith("-")
            ]
            added_lines = [line[1:] for line in hunk_lines
                           if line.startswith("+")]
            meta = {
                "added_lines": added_lines,
                "first_change": first_change,
                "next_change": next_change,
                "prev_change": prev_change
            }
            return (deleted_lines, start, size, meta)
        return ([], -1, -1, {})

    def untracked(self):
        """Determine whether the view shows an untracked file."""
        return self.handle_files([])

    def ignored(self):
        """Determine whether the view shows an ignored file."""
        return self.handle_files(['-i'])

    def handle_files(self, additional_args):
        """Run git ls-files to check for untracked or ignored file."""
        if self._git_tree:
            def is_nonempty(results):
                """Determine if view's file is in git's index.

                If the view's file is not part of the index
                git returns empty output to stdout.
                """
                return bool(results)

            args = [
                self.settings.git_binary,
                'ls-files', '--other', '--exclude-standard',
            ] + additional_args + [
                os.path.join(self._git_tree, self._git_path),
            ]
            args = list(filter(None, args))  # Remove empty args
            return self.execute_async(args).then(is_nonempty)
        return Promise.resolve(False)

    def git_commits(self):
        r"""Query all commits.

        The git output will have following format splitted by \a:
            <hash> <title>
            <name> <email>
            <date> (<time> ago)
        """
        args = [
            self.settings.git_binary,
            'log', '--all',
            '--pretty=%h %s\a%an <%aE>\a%ad (%ar)',
            '--date=local', '--max-count=9000'
        ]
        return self.execute_async(args)

    def git_file_commits(self):
        r"""Query all commits with changes to the attached file.

        The git output will have following format splitted by \a:
            <timestamp>
            <hash> <title>
            <name> <email>
            <date> (<time> ago)
        """
        args = [
            self.settings.git_binary,
            'log',
            '--pretty=%at\a%h %s\a%an <%aE>\a%ad (%ar)',
            '--date=local', '--max-count=9000',
            '--', self._git_path
        ]
        return self.execute_async(args)

    def git_branches(self):
        """Query all branches of the file's repository."""
        args = [
            self.settings.git_binary,
            'for-each-ref',
            '--sort=-committerdate',
            '--format=%(subject)\a%(refname)\a%(objectname)',
            'refs/heads/'
        ]
        return self.execute_async(args)

    def git_tags(self):
        """Query all tags of the file's repository."""
        args = [
            self.settings.git_binary,
            'show-ref',
            '--tags',
            '--abbrev=7'
        ]
        return self.execute_async(args)

    def git_current_branch(self):
        """Query the current branch of the file's repository."""
        if self._git_branch:
            return Promise.resolve(self._git_branch)

        def cache_result(branch):
            self._git_branch = branch
            return branch

        args = [
            self.settings.git_binary,
            'rev-parse',
            '--abbrev-ref',
            'HEAD'
        ]
        return self.execute_async(args).then(cache_result)

    def git_compare_commit(self, compare_against):
        """Query the commit hash of the compare target.

        Arguments:
            compare_against  - The reference to compare against if not a hash.
        """
        args = [
            self.settings.git_binary,
            'rev-parse',
            compare_against
        ]
        return self.execute_async(args)

    def git_read_file(self, commit):
        """Read the content of the file from specific commit.

        This method uses `git archive` to read the file content from git index
        to enable support of smudge filters (fixes Issue #74). Git applies
        smudge filters to some commands like `archive`, `diff` and `checkout`
        only, but not to commands like `show`.

        Arguments:
            commit (string): The identifier of the commit to read file from.

        Returns:
            Promise: A promise to read and unzip the content of a file from git
                index which will be resolved with the inflated file content.
        """
        def unzip(output):
            """Unzip file binary content from git output.

            Arguments:
                output (string): Binary output returned by git containing the
                    zipped content of the read file or None on error.

            Returns:
                string: Unzipped file content or None if git didn't return
                    zipped file content. Error is already printed in that case.
            """
            try:
                # Extract file contents from zipped archive.
                # The `filelist` contains numerous directories finalized
                # by exactly one file whose content we are interested in.
                archive = zipfile.ZipFile(BytesIO(output))
                return archive.read(archive.filelist[-1])
            except:
                return None

        args = [
            self.settings.git_binary,
            'archive', '--format=zip',
            commit, self._git_path
        ]
        return self.execute_async(args=args, decode=False).then(unzip)

    def execute_async(self, args, decode=True):
        """Execute a git command asynchronously and return a Promise.

        Arguments:
            args (list): The command line arguments used to run git.
            decode (bool): If True the git's output is decoded assuming utf-8
                      which is the default output encoding of git.

        Returns:
            Promise: A promise to return the git output in the future.
        """
        def executor(resolve):
            set_timeout(lambda: resolve(self.execute(args, decode)), 10)
        return Promise(executor)

    def execute(self, args, decode=True):
        """Execute a git command synchronously and return its output.

        Arguments:
            args (list): The command line arguments used to run git.
            decode (bool): If True the git's output is decoded assuming utf-8
                      which is the default output encoding of git.

        Returns:
            string: The decoded or undecoded output read from stdout.
        """
        stdout, stderr = None, None

        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            proc = subprocess.Popen(
                args=args, cwd=self._git_tree, startupinfo=startupinfo,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                stdin=subprocess.PIPE)
            if _HAVE_TIMEOUT:
                stdout, stderr = proc.communicate(timeout=30)
            else:
                stdout, stderr = proc.communicate()
        except OSError as error:
            # print out system error message
            print('GitGutter: "git %s" failed with "%s"' % (args[1], error))
        except TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
        # handle empty git output
        if not stdout:
            if stderr and self.settings.get('debug'):
                print('GitGutter: "git %s" failed with "%s"' % (
                    args[1], stderr.decode('utf-8').strip()))
            return stdout
        # return decoded ouptut using utf-8 or binary output
        return stdout.decode('utf-8').strip() if decode else stdout
