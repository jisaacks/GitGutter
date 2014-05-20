import os
import sublime
import subprocess
import encodings
import re

try:
    from GitGutter import git_helper
    from GitGutter.view_collection import ViewCollection
except ImportError:
    import git_helper
    from view_collection import ViewCollection


class GitGutterHandler:

    def __init__(self, view):
        self.load_settings()
        self.view = view
        self.git_temp_file = ViewCollection.git_tmp_file(self.view)
        self.buf_temp_file = ViewCollection.buf_tmp_file(self.view)
        self.stg_temp_file = ViewCollection.stg_tmp_file(self.view)
        if self.on_disk():
            self.git_tree = git_helper.git_tree(self.view)
            self.git_dir = git_helper.git_dir(self.git_tree)
            self.git_path = git_helper.git_file_path(self.view, self.git_tree)

    def _get_view_encoding(self):
        # get encoding and clean it for python ex: "Western (ISO 8859-1)"
        # NOTE(maelnor): are we need regex here?
        pattern = re.compile(r'.+\((.*)\)')
        encoding = self.view.encoding()
        if pattern.match(encoding):
            encoding = pattern.sub(r'\1', encoding)

        encoding = encoding.replace('with BOM', '')
        encoding = encoding.replace('Windows', 'cp')
        encoding = encoding.replace('-', '_')
        encoding = encoding.replace(' ', '')
        return encoding

    def on_disk(self):
        # if the view is saved to disk
        return self.view.file_name() is not None

    def reset(self):
        if self.on_disk() and self.git_path and self.view.window():
            self.view.window().run_command('git_gutter')

    def get_git_path(self):
        return self.git_path

    def update_buf_file(self):
        chars = self.view.size()
        region = sublime.Region(0, chars)

        # Try conversion
        try:
            contents = self.view.substr(
                region).encode(self._get_view_encoding())
        except UnicodeError:
            # Fallback to utf8-encoding
            contents = self.view.substr(region).encode('utf-8')
        except LookupError:
            # May encounter an encoding we don't have a codec for
            contents = self.view.substr(region).encode('utf-8')

        contents = contents.replace(b'\r\n', b'\n')
        contents = contents.replace(b'\r', b'\n')
        f = open(self.buf_temp_file.name, 'wb')

        f.write(contents)
        f.close()

    def update_stg_file(self):
        # FIXME dry up duplicate in update_stg_file and update_git_file

        # the git repo won't change that often
        # so we can easily wait 5 seconds
        # between updates for performance
        if ViewCollection.stg_time(self.view) > 5:
            open(self.stg_temp_file.name, 'w').close()
            args = [
                self.git_binary_path,
                '--git-dir=' + self.git_dir,
                '--work-tree=' + self.git_tree,
                'show',
                ':' + self.git_path,
            ] 
            try:
                contents = self.run_command(args)
                contents = contents.replace(b'\r\n', b'\n')
                contents = contents.replace(b'\r', b'\n')
                f = open(self.stg_temp_file.name, 'wb')
                f.write(contents)
                f.close()
                ViewCollection.update_stg_time(self.view)
            except Exception:
                pass

    def update_git_file(self):
        # the git repo won't change that often
        # so we can easily wait 5 seconds
        # between updates for performance
        if ViewCollection.git_time(self.view) > 5:
            open(self.git_temp_file.name, 'w').close()
            args = [
                self.git_binary_path,
                '--git-dir=' + self.git_dir,
                '--work-tree=' + self.git_tree,
                'show',
                ViewCollection.get_compare() + ':' + self.git_path,
            ]
            try:
                contents = self.run_command(args)
                contents = contents.replace(b'\r\n', b'\n')
                contents = contents.replace(b'\r', b'\n')
                f = open(self.git_temp_file.name, 'wb')
                f.write(contents)
                f.close()
                ViewCollection.update_git_time(self.view)
            except Exception:
                pass

    def total_lines(self):
        chars = self.view.size()
        region = sublime.Region(0, chars)
        lines = self.view.lines(region)
        return len(lines)

    # Parse unified diff with 0 lines of context.
    # Hunk range info format:
    #   @@ -3,2 +4,0 @@
    #     Hunk originally starting at line 3, and occupying 2 lines, now
    #     starts at line 4, and occupies 0 lines, i.e. it was deleted.
    #   @@ -9 +10,2 @@
    #     Hunk size can be omitted, and defaults to one line.
    # Dealing with ambiguous hunks:
    #   "A\nB\n" -> "C\n"
    #   Was 'A' modified, and 'B' deleted? Or 'B' modified, 'A' deleted?
    #   Or both deleted? To minimize confusion, let's simply mark the
    #   hunk as modified.
    def process_diff(self, diff_str):
        inserted = []
        modified = []
        deleted = []
        adj_map = {0:0}
        hunk_re = '^@@ \-(\d+),?(\d*) \+(\d+),?(\d*) @@'
        hunks = re.finditer(hunk_re, diff_str, re.MULTILINE)
        for hunk in hunks:
            old_start = int(hunk.group(1))
            new_start = int(hunk.group(3))
            old_size = int(hunk.group(2) or 1)
            new_size = int(hunk.group(4) or 1)
            if not old_size:
                inserted += range(new_start, new_start + new_size)
            elif not new_size:
                deleted += [new_start + 1]
            else:
                modified += range(new_start, new_start + new_size)
            # Add values to adjustment map
            k = old_start + sum(adj_map.values())
            v = new_size - old_size
            adj_map[k] = v
        if len(inserted) == self.total_lines() and not self.show_untracked:
            # All lines are "inserted"
            # this means this file is either:
            # - New and not being tracked *yet*
            # - Or it is a *gitignored* file
            return ([], [], [], {0:0})
        else:
            return (inserted, modified, deleted, adj_map)

    def diff(self):
        if self.on_disk() and self.git_path:
            self.update_git_file()
            self.update_buf_file()
            args = [
                self.git_binary_path, 'diff', '-U0', '--no-color',
                self.ignore_whitespace,
                self.patience_switch,
                self.git_temp_file.name,
                self.buf_temp_file.name,
            ]
            args = list(filter(None, args))  # Remove empty args
            results = self.run_command(args)
            encoding = self._get_view_encoding()
            try:
                decoded_results = results.decode(encoding.replace(' ', ''))
            except UnicodeError:
                decoded_results = results.decode("utf-8")
            return self.process_diff(decoded_results)[:3]
        else:
            return ([], [], [])

    # FIXME
    # Refactor staged/diff methods to dry up duplicated code
    def unstaged(self):
        if self.on_disk() and self.git_path:
            self.update_stg_file()
            self.update_buf_file()
            args = [
                self.git_binary_path, 'diff', '-U0', '--no-color',
                self.stg_temp_file.name,
                self.buf_temp_file.name
            ]
            args = list(filter(None, args))  # Remove empty args
            results = self.run_command(args)
            encoding = self._get_view_encoding()
            try:
                decoded_results = results.decode(encoding.replace(' ', ''))
            except UnicodeError:
                decoded_results = results.decode("utf-8")
            processed = self.process_diff(decoded_results)
            ViewCollection.set_line_adjustment_map(self.view,processed[3])
            return processed[:3]
        else:
            return ([], [], [])

    def staged(self):
        if self.on_disk() and self.git_path:
            self.update_stg_file()
            self.update_buf_file()
            args = [
                self.git_binary_path, 'diff', '-U0', '--no-color', '--staged',
                ViewCollection.get_compare(),
                self.git_path
            ]
            args = list(filter(None, args))  # Remove empty args
            results = self.run_command(args)
            encoding = self._get_view_encoding()
            try:
                decoded_results = results.decode(encoding.replace(' ', ''))
            except UnicodeError:
                decoded_results = results.decode("utf-8")
            diffs = self.process_diff(decoded_results)[:3]
            return self.apply_line_adjustments(*diffs)
        else:
            return ([], [], [])

    def apply_line_adjustments(self, inserted, modified, deleted):
        adj_map = ViewCollection.get_line_adjustment_map(self.view)
        i = inserted
        m = modified
        d = deleted
        for k in sorted(adj_map.keys()):
            at_line = k
            lines_added = adj_map[k]
            # `lines_added` lines were added at line `at_line`
            # Each line in the diffs that are above `at_line` add `lines_added`
            i = [l + lines_added if l > at_line else l for l in i]
            m = [l + lines_added if l > at_line else l for l in m]
            d = [l + lines_added if l > at_line else l for l in d]
        return (i,m,d)

    def untracked(self):
        return self.handle_files([])

    def ignored(self):
        return self.handle_files(['-i'])

    def handle_files(self, additionnal_args):
        if self.show_untracked and self.on_disk() and self.git_path:
            args = [
                self.git_binary_path,
                '--git-dir=' + self.git_dir,
                '--work-tree=' + self.git_tree,
                'ls-files', '--other', '--exclude-standard',
            ] + additionnal_args + [
                os.path.join(self.git_tree, self.git_path),
            ]
            args = list(filter(None, args))  # Remove empty args
            results = self.run_command(args)
            encoding = self._get_view_encoding()
            try:
                decoded_results = results.decode(encoding.replace(' ', ''))
            except UnicodeError:
                decoded_results = results.decode("utf-8")
            return (decoded_results != "")
        else:
            return False

    def has_stages(self):
        args = [self.git_binary_path, 
                '--git-dir=' + self.git_dir,
                '--work-tree=' + self.git_tree,
                'diff', '--staged']
        results = self.run_command(args)
        if len(results):
            return True
        else:
            return False

    def git_commits(self):
        args = [
            self.git_binary_path,
            '--git-dir=' + self.git_dir,
            '--work-tree=' + self.git_tree,
            'log', '--all',
            '--pretty=%s\a%h %an <%aE>\a%ad (%ar)',
            '--date=local', '--max-count=9000'
        ]
        results = self.run_command(args)
        return results

    def git_branches(self):
        args = [
            self.git_binary_path,
            '--git-dir=' + self.git_dir,
            '--work-tree=' + self.git_tree,
            'for-each-ref',
            '--sort=-committerdate',
            '--format=%(subject)\a%(refname)\a%(objectname)',
            'refs/heads/'
        ]
        results = self.run_command(args)
        return results

    def git_tags(self):
        args = [
            self.git_binary_path,
            '--git-dir=' + self.git_dir,
            '--work-tree=' + self.git_tree,
            'show-ref',
            '--tags',
            '--abbrev=7'
        ]
        results = self.run_command(args)
        return results

    def run_command(self, args):
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        proc = subprocess.Popen(args, stdout=subprocess.PIPE,
                                startupinfo=startupinfo, stderr=subprocess.PIPE)
        return proc.stdout.read()

    def load_settings(self):
        self.settings = sublime.load_settings('GitGutter.sublime-settings')
        self.user_settings = sublime.load_settings(
            'Preferences.sublime-settings')

        # Git Binary Setting
        self.git_binary_path = 'git'
        git_binary = self.user_settings.get(
            'git_binary') or self.settings.get('git_binary')
        if git_binary:
            self.git_binary_path = git_binary

        # Ignore White Space Setting
        self.ignore_whitespace = self.settings.get('ignore_whitespace')
        if self.ignore_whitespace == 'all':
            self.ignore_whitespace = '-w'
        elif self.ignore_whitespace == 'eol':
            self.ignore_whitespace = '--ignore-space-at-eol'
        else:
            self.ignore_whitespace = ''

        # Patience Setting
        self.patience_switch = ''
        patience = self.settings.get('patience')
        if patience:
            self.patience_switch = '--patience'

        # Untracked files
        self.show_untracked = self.settings.get(
            'show_markers_on_untracked_file')
