# -*- coding: utf-8 -*-
import codecs
import functools
import os
import re
import subprocess

try:
    from subprocess import TimeoutExpired
    _HAVE_TIMEOUT = True
except ImportError:
    class TimeoutExpired(Exception):
        pass
    _HAVE_TIMEOUT = False

import sublime

from . import path
from . import utils
from .promise import Promise
from .promise import PromiseError
from .temp import TempFile
from .utils import WIN32
from .view import GitGutterViewCache

# The view class has a method called 'change_count()'
_HAVE_VIEW_CHANGE_COUNT = hasattr(sublime.View, "change_count")

# Compiled regex pattern to parse first `git status -s -b` line.
#
#     (\S+(?=\.{3})|\S+(?!\.{3}$))
#         The local branch consists of any none whitespace character followed
#         by three dots or located at the end of string without containing them.
#
#     \.{3}(\S+)
#         If three dots are found, the tracked remote follows them.
#
#     \[(?:ahead (\d+))?(?:, )?(?:behind (\d+))?\]
#         If a tracked remote exists, the number of commits the local branch is
#         ahead and behind the remote is optionally available, too.
_STATUS_RE = re.compile(r'## (\S+(?=\.{3})|\S+(?!\.{3}$))(?:\.{3}(\S+)(?: \[(?:ahead (\d+))?(?:, )?(?:behind (\d+))?\])?)?')

_BUFSIZE = 2**15

try:
    set_timeout = sublime.set_timeout_async
except AttributeError:
    set_timeout = sublime.set_timeout


class GitGutterHandler(object):

    # The list of all instances' binaries which don't work properly.
    # For each view/project a unique "git_binary" setting can be applied.
    # To display error messages only once per binary, none working binaries
    # need to be tracked here.
    _missing_binaries = set()

    # The working tree / compare target map as class wide attribute.
    # It is initialized once and keeps the values of all object instantces.
    _compare_against_mapping = {}

    def __init__(self, view, settings):
        """Initialize GitGutterHandler object."""
        self.settings = settings
        # attached view being tracked
        self.view = view
        # the view content being mirrored to disk
        self.view_cache = GitGutterViewCache(view)
        # cached view file name to detect renames
        self._view_file_name = None
        # path to temporary file with git index content
        self._git_temp_file = None
        # temporary file contains up to date information
        self._git_temp_file_valid = False
        # real path to current work tree
        self._git_tree = None
        # relative file path in work tree
        self._git_path = None
        # file is part of the git repository
        self.git_tracked = False
        # compare target commit hash
        self._git_compared_commit = None
        # cached git diff result for diff popup
        self._git_diff_cache = ''
        # cached git binary checked for version
        self._git_binary = None
        # PEP-440 conform git version (major, minor, patch)
        self._git_version = None
        # local dictionary of environment variables
        self._git_env = None
        # git is accessed via WSL on Windows 10
        self._git_wsl = False

    def version(self, validate):
        """Return git executable version.

        The version string is used to check, whether git executable exists and
        works properly. It may also be used to enable functions with newer git
        versions.

        As the "git_binary" setting may be view/project specific and may change
        at each time it needs to be checked in proper situations to validate
        whether git still works properly.

        Arguments:
            validate (bool): If True force updating version string. Use cached
                value otherwise.
        Returns:
            tuple: PEP-440 conform git version (major, minor, patch)
        """
        if not validate:
            return self._git_version

        # check if the git binary setting has changed
        git_binary = self.settings.git_binary
        if self._git_binary != git_binary:
            self._git_binary = git_binary
            self._git_version = None
            # a unix like path on windows means running git via WSL
            self._git_wsl = WIN32 and self._git_binary.startswith('/')

        if self._git_version is None:
            is_missing = self._git_binary in self._missing_binaries
            git_version = ''

            # Query git version synchronously
            try:
                proc = self.popen([self._git_binary, '--version'])
                if _HAVE_TIMEOUT:
                    proc.wait(1.0)
                git_version = proc.stdout.read().decode('utf-8')

            except TimeoutExpired as error:
                proc.kill()
                git_version = proc.stdout.read().decode('utf-8')
                if not is_missing and self.settings.get('debug'):
                    utils.log_message(str(error))

            except Exception as error:
                if not is_missing and self.settings.get('debug'):
                    utils.log_message(str(error))

            # Parse version string like (git version 2.12.2.windows.1)
            match = re.match(r'git version (\d+)\.(\d+)\.(\d+)', git_version)
            if match:
                # PEP-440 conform git version (major, minor, patch)
                self._git_version = tuple(int(g) for g in match.groups())
                if is_missing:
                    utils.log_message(self._git_binary + ' is back on duty!')
                    self._missing_binaries.discard(self._git_binary)

            elif not is_missing:
                utils.log_message(self._git_binary + ' not found or working!')
                if self.settings.get('debug'):
                    utils.log_message(
                        '"git --version" returned "{}"'.format(git_version))
                self._missing_binaries.add(self._git_binary)

        return self._git_version

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

    def work_tree_supported(self):
        """The path of the working directory is accessible by git.

        Windows Subsystem for Linux automatically maps local drive letters to
        /mnt only. UNC paths would need to be mounted manually, which is not
        supported by GitGutter at the moment.

        Returns:
            bool:
                True if not running in WSL mode or path is a local drive
                False if the working tree is no local drive in WSL mode.
        """
        return not self._git_wsl or self._git_tree and self._git_tree[1] == ':'

    def translate_path_to_wsl(self, filename):
        """Translate filename to a WSL compatible unix path on demand.

        Arguments:
            filename (string):
                The path string to optionally translate to unix style.

        Returns:
            string:
                A unix like path if git is executed via Windows Subsystem for
                Linux (WSL) on a Windows 10 machine or `filename` otherwise.
        """
        return path.translate_to_wsl(filename) if self._git_wsl else filename

    def is_rebase_active(self):
        """Returns True if a rebase is active in the repository."""
        return os.path.exists(
            os.path.join(self._git_tree, '.git', 'rebase-merge'))

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

    def in_repo(self):
        """Return true, if the most recent `git show` returned any content.

        If `git show` returns empty content, any diff will result in
        all lines added state and the view's file is most commonly untracked.
        """
        return self.git_tracked

    def is_git_file_valid(self):
        """Return True if temporary file is marked up to date."""
        return self._git_temp_file_valid

    def invalidate_git_file(self):
        """Invalidate all cached results of recent git commands."""
        self._git_temp_file_valid = False
        self._git_env = None

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
            functools.partial(self._check_git_file, compared_id))

    def _check_git_file(self, compared_id, output):
        """Check the result of the git cat-file command.

        The function resolves the promise with True to indicate the
        updated git file.

        Arguments:
            compared_id (string): The new compare target's object id to store.
            output (integer): The size of the file.
                   (PromiseError): An error object indicating failure.

        Returns:
            bool: True if file was written to disc successfully.
        """
        if isinstance(output, PromiseError):
            utils.log_message('failed to create git cache! %s' % output)
            return False

        self._git_compared_commit = compared_id
        self.git_tracked = output > 0
        return self.git_tracked

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
        updated_view_file = self.view_cache.update()
        if not updated_git_file and not updated_view_file:
            return self.process_diff(self._git_diff_cache)

        if not self._git_temp_file:
            return self.process_diff(self._git_diff_cache)

        return self.execute_async(list(filter(None, (
            self._git_binary,
            '-c', 'core.autocrlf=input',
            '-c', 'core.eol=lf',
            '-c', 'core.safecrlf=false',
            'diff', '-U0', '--no-color', '--no-index',
            self.settings.ignore_whitespace,
            self.settings.diff_algorithm,
            self.translate_path_to_wsl(self._git_temp_file.name),
            self.translate_path_to_wsl(self.view_cache.name)
        ))), decode=False).then(self._decode_diff)

    def _decode_diff(self, results):
        encoding = self.view_cache.python_friendly_encoding()
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
        return self.execute_async([
            self._git_binary,
            'ls-files', '--other', '--exclude-standard',
            self._git_path
        ]).then(lambda x: bool(x))

    def ignored(self):
        """Determine whether the view shows an ignored file."""
        return self.execute_async([
            self._git_binary,
            'ls-files', '--other', '--exclude-standard', '-i',
            self._git_path
        ]).then(lambda x: bool(x))

    def git_commits(self):
        r"""Query all commits.

        The git output will have following format splitted by \a:
            <hash> <title>
            <name> <email>
            <date> (<time> ago)
        """
        return self.execute_async([
            self._git_binary,
            'log', '--all',
            '--pretty="%h | %s\a%an <%aE>\a%ad (%ar)"',
            '--date=local', '--max-count=9000'
        ])

    def git_file_commits(self):
        r"""Query all commits with changes to the attached file.

        The git output will have following format splitted by \a:
            <timestamp>
            <hash> <title>
            <name> <email>
            <date> (<time> ago)
        """
        return self.execute_async([
            self._git_binary,
            'log',
            '--pretty="%at\a%h | %s\a%an <%aE>\a%ad (%ar)"',
            '--date=local', '--max-count=9000',
            '--', self._git_path
        ])

    def git_branches(self):
        """Query all branches of the file's repository."""
        template = (
            '--format="%(refname)\a%(objectname:short) | %(subject)'
            '\a%(committername) %(committeremail)\a%(committerdate)"'
        )
        return self.execute_async([
            self._git_binary,
            'for-each-ref', '--sort=-committerdate', template, 'refs/heads/'
        ])

    def git_tags(self):
        """Query all tags of the file's repository.

        Use the plumping for-each-ref to read the tag information.
        Both tagger- and committer- name/date are read because the first one
        is valid for annoted and later for simple tags.
        """
        template = (
            '--format="%(refname)\a%(objectname:short) | %(subject)'
            '\a%(taggername) %(taggeremail)\a%(taggerdate)'
            '\a%(committername) %(committeremail)\a%(committerdate)"'
        )
        return self.execute_async([
            self._git_binary,
            'for-each-ref', '--sort=-refname', template, 'refs/tags/'
        ])

    def git_branch_status(self):
        """Query the current status of the file's repository."""
        def parse_output(output):
            """Parse output of git status and cache the value."""
            added, deleted, modified, staged = 0, 0, 0, 0
            try:
                lines = output.split('\n')
                # parse branch line
                match = _STATUS_RE.match(lines[0])
                branch, remote, ahead, behind = match.groups()
                # parse file stats
                for line in lines:
                    if line:
                        w = line[1]
                        added += w == '?'
                        deleted += w == 'D'
                        modified += w == 'M'
                        staged += line[0] in 'ADMR'
            except:
                branch, remote, ahead, behind = 'unknown', None, 0, 0

            return {
                'branch': branch,
                'remote': remote,
                'ahead': int(ahead or 0),
                'behind': int(behind or 0),
                'added_files': added,
                'deleted_files': deleted,
                'modified_files': modified,
                'staged_files': staged
            }

        return self.execute_async([
            self._git_binary,
            '-c', 'color.status=never',
            'status', '-b', '-s', '-u'
        ]).then(parse_output)

    def git_compare_commit(self, compare_against):
        """Query the commit hash of the compare target.

        Arguments:
            compare_against  - The reference to compare against if not a hash.
        """
        return self.execute_async([
            self._git_binary, 'rev-parse', compare_against])

    def git_blame(self, row):
        """Call git blame to find out who changed a specific line of code"""
        if self.settings.get('line_annotation_ignore_whitespace'):
            ignore_ws = ['-w']
        else:
            ignore_ws = []

        return self.execute_async([
            self._git_binary,
            '-c', 'core.autocrlf=input',
            '-c', 'core.eol=lf',
            '-c', 'core.safecrlf=false',
            'blame', '-p', '-L%d,%d' % (row + 1, row + 1)
        ] + ignore_ws + [
            '--contents', self.translate_path_to_wsl(self.view_cache.name),
            '--', self._git_path
        ])

    def git_read_file(self, commit):
        """Read the content of the file from specific commit.

        This method uses `git cat-files` to read the file content from git
        index to enable support of smudge filters (fixes Issue #74). Git
        applies smudge filters to some commands like `archive`, `diff`,
        `checkout` and `cat-file` only, but not to commands like `show`.

        Arguments:
            commit (string): The identifier of the commit to read file from.

        Returns:
            Promise: A promise to read the content of a file from git index.

            The Promise resolves with the number of bytes written to the cache
            in case of success.

            The Promise resolves with PromiseError if the cache file could not
            be created, opened or written data to, if git failed to run or
            returned a none-zero exit code other than 128 (file not found).
        """
        if not self._git_temp_file:
            self._git_temp_file = TempFile(mode='wb')

        try:
            proc = self.popen([
                self._git_binary,
                '-c', 'core.autocrlf=input',
                '-c', 'core.eol=lf',
                '-c', 'core.safecrlf=false',
                'cat-file',
                # smudge filters are supported with git 2.11.0+ only
                '--filters' if self._git_version >= (2, 11, 0) else '-p',
                ':'.join((commit, self._git_path))
            ], stdout=self._git_temp_file.open())

        except Exception as error:
            self._git_temp_file.close()
            return Promise.resolve(PromiseError(str(error)))

        def poll(proc, resolve):
            """Poll the process and resolve promise if finished."""
            try:
                returncode = proc.poll()
                if returncode is None:
                    # git is still busy, come here later again
                    set_timeout(functools.partial(poll, proc, resolve), 50)
                    return None

                # file is still open for writing at this point
                with self._git_temp_file as file:
                    if returncode == 0:
                        # resolve with the number of bytes got from git cat-file
                        return resolve(file.tell())
                    elif returncode == 128:
                        # resolve with 0 bytes if file was not found in repo.
                        return resolve(0)
                    return resolve(PromiseError("git returned error %d: %s" % (
                        returncode, proc.stderr.read().decode('utf-8'))))

            except Exception as error:
                # close the temporary file if anything goes wrong
                self._git_temp_file.close()
                raise

        def executor(resolve):
            """Start polling the process to query for its finish."""
            set_timeout(functools.partial(poll, proc, resolve), 50)

        return Promise(executor)

    def execute_async(self, args, decode=True):
        """Execute a git command asynchronously and return a Promise.

        Arguments:
            args (list): The command line arguments used to run git.
            decode (bool): If True the git's output is decoded assuming utf-8
                      which is the default output encoding of git.

        Returns:
            Promise: A promise to return the git output in the future.
        """
        try:
            proc = self.popen(args)
        except Exception as error:
            utils.log_message(str(error))
            return Promise.resolve(None)

        # inject some attributes into the proc object
        setattr(proc, 'buffer', b'')

        def poll(proc, resolve, decode):
            """Poll the process and resolve promise if finished.

            Arguments:
                proc (subprocess.Popen):
                    The running process' object to quiery for completion
                resolve (callable):
                    The function to be called to resolve the Promise.
                decode (bool):
                    True to decode the binary output to text.
            """
            chunk = proc.stdout.read(_BUFSIZE)
            if chunk:
                # need to read from stdout as process won't exit if buffer
                # is full.
                proc.buffer += chunk
                if len(chunk) == _BUFSIZE:
                    # git is still busy, come here later again
                    set_timeout(functools.partial(
                        poll, proc, resolve, decode), 20)
                    return

            if not proc.buffer and self.settings.get('debug'):
                proc.wait()
                # 0 = ok, 128 = file not found
                if proc.returncode not in (0, 128):
                    utils.log_message('%s failed with "%s"' % (
                        ' '.join(args), proc.stderr.read().decode('utf-8').strip()))

            # return decoded ouptut using utf-8 or binary output
            if decode and proc.buffer is not None:
                return resolve(proc.buffer.decode('utf-8').strip())
            return resolve(proc.buffer)

        def executor(resolve):
            """Start polling the process to query for its finish."""
            set_timeout(functools.partial(poll, proc, resolve, decode), 20)

        return Promise(executor)

    def popen(self, args, stdout=subprocess.PIPE):
        """Prepare the environment and spawn the subprocess.

        Arguments:
            args (list):
                A list of arguments to pass to `subprocess.Popen`.
            stdout (int or stream):
                The target of the output of the spawned subprocess.
                It defaults to `subprocess.PIPE` to retrieve output via stdout,
                but can also be a filestream to directly write the content to
                a file on disk.
        Returns:
            subprocess.Popen: The object of the spawned subprocess.
        """
        startupinfo = None
        if WIN32:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # run git through wsl.exe
        if self._git_wsl:
            args.insert(0, "wsl")

        # update private environment
        if self._git_env is None:
            self._git_env = os.environ.copy()
            for key, value in self.settings.get('env', {}).items():
                if value is None:
                    del self._git_env[key]
                else:
                    self._git_env[key] = str(value)

        return subprocess.Popen(
            args=args,
            cwd=self._git_tree,
            env=self._git_env,
            bufsize=_BUFSIZE,
            startupinfo=startupinfo,
            stdin=subprocess.PIPE,   # python 3.3 bug on Win7
            stderr=subprocess.PIPE,
            stdout=stdout
        )
