import os
import subprocess
import re
import codecs
import time
import threading
import sublime
import tempfile

try:
    from . import git_helper
    from .promise import Promise, ConstPromise
except (ImportError, ValueError):
    import git_helper
    from promise import Promise, ConstPromise

class GitGutterHandler:
    # the git repo won't change that often
    # so we can easily wait  seconds
    # between updates for performance
    GitFileUpdateIntervalSecs = 5

    def __init__(self, view, settings):
        self.view = view
        self.settings = settings

        self.git_temp_file = tempfile.NamedTemporaryFile()
        self.git_temp_file.close()

        self.buf_temp_file = tempfile.NamedTemporaryFile()
        self.buf_temp_file.close()

        self.git_tree = None
        self.git_dir = None
        self.git_path = None

        self.clear_git_time()

    def clear_git_time(self):
        self.last_refresh_time_git_file = time.time() - (self.GitFileUpdateIntervalSecs + 1)

    def update_git_time(self):
        self.last_refresh_time_git_file = time.time()

    def git_time(self):
        return time.time() - self.last_refresh_time_git_file

    def _get_view_encoding(self):
        # get encoding and clean it for python ex: "Western (ISO 8859-1)"
        # NOTE(maelnor): are we need regex here?
        pattern = re.compile(r'.+\((.*)\)')
        encoding = self.view.encoding()
        if encoding == "Undefined":
            encoding = self.view.settings().get('default_encoding')
        if pattern.match(encoding):
            encoding = pattern.sub(r'\1', encoding)

        encoding = encoding.replace('with BOM', '')
        encoding = encoding.replace('Windows', 'cp')
        encoding = encoding.replace('-', '_')
        encoding = encoding.replace(' ', '')

        # work around with ConvertToUTF8 plugin
        origin_encoding = self.view.settings().get('origin_encoding')
        return origin_encoding or encoding

    def on_disk(self):
        # if the view is saved to disk
        on_disk = self.view.file_name() is not None
        if on_disk:
            self.git_tree = self.git_tree or git_helper.git_tree(self.view)
            self.git_dir = self.git_dir or git_helper.git_dir(self.git_tree)
            self.git_path = self.git_path or git_helper.git_file_path(
                self.view, self.git_tree
            )
        return on_disk

    def reset(self):
        if self.on_disk() and self.git_path:
            self.view.run_command('git_gutter')

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

        if self.view.encoding() == "UTF-8 with BOM":
            f.write(codecs.BOM_UTF8)

        f.write(contents)
        f.close()

    def update_git_file(self):
        if self.git_time() > self.GitFileUpdateIntervalSecs:
            open(self.git_temp_file.name, 'w').close()
            args = [
                self.settings.git_binary_path,
                '--git-dir=' + self.git_dir,
                '--work-tree=' + self.git_tree,
                'show',
                self.settings.get_compare_against(self.git_dir) + ':' + self.git_path,
            ]
            def write_file(contents):
                contents = contents.replace(b'\r\n', b'\n')
                contents = contents.replace(b'\r', b'\n')
                f = open(self.git_temp_file.name, 'wb')
                f.write(contents)
                f.close()
            try:
                self.update_git_time()
                return self.run_command(args).addCallback(write_file)
            except Exception:
                print('got exception')
                pass
        else:
            return ConstPromise(None)

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
        hunk_re = '^@@ \-(\d+),?(\d*) \+(\d+),?(\d*) @@'
        hunks = re.finditer(hunk_re, diff_str, re.MULTILINE)
        for hunk in hunks:
            start = int(hunk.group(3))
            old_size = int(hunk.group(2) or 1)
            new_size = int(hunk.group(4) or 1)
            if not old_size:
                inserted += range(start, start + new_size)
            elif not new_size:
                deleted += [start + 1]
            else:
                modified += range(start, start + new_size)
        return (inserted, modified, deleted)

    def diff(self):
        if self.on_disk() and self.git_path:
            def decode_and_process_diff(results):
                encoding = self._get_view_encoding()
                try:
                    decoded_results = results.decode(encoding.replace(' ', ''))
                except UnicodeError:
                    try:
                        decoded_results = results.decode("utf-8")
                    except UnicodeDecodeError:
                        decoded_results = ""
                except LookupError:
                    try:
                        decoded_results = codecs.decode(results)
                    except UnicodeDecodeError:
                        decoded_results = ""
                return self.process_diff(decoded_results)

            def run_diff(_unused):
                self.update_buf_file()
                args = [
                    self.settings.git_binary_path, 'diff', '-U0', '--no-color', '--no-index',
                    self.settings.ignore_whitespace,
                    self.settings.patience_switch,
                    self.git_temp_file.name,
                    self.buf_temp_file.name,
                ]
                args = list(filter(None, args))  # Remove empty args
                return self.run_command(args).map(decode_and_process_diff)
            return self.update_git_file().flatMap(run_diff)
        else:
            return ConstPromise(([], [], []))

    def untracked(self):
        return self.handle_files([])

    def ignored(self):
        return self.handle_files(['-i'])

    def handle_files(self, additionnal_args):
        if self.on_disk() and self.git_path:
            def is_nonempty(results):
                encoding = self._get_view_encoding()
                try:
                    decoded_results = results.decode(encoding.replace(' ', ''))
                except UnicodeError:
                    decoded_results = results.decode("utf-8")
                return (decoded_results != "")
            args = [
                self.settings.git_binary_path,
                '--git-dir=' + self.git_dir,
                '--work-tree=' + self.git_tree,
                'ls-files', '--other', '--exclude-standard',
            ] + additionnal_args + [
                os.path.join(self.git_tree, self.git_path),
            ]
            args = list(filter(None, args))  # Remove empty args
            return self.run_command(args).map(is_nonempty)
        else:
            return ConstPromise(False)

    def git_commits(self):
        args = [
            self.settings.git_binary_path,
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
            self.settings.git_binary_path,
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
            self.settings.git_binary_path,
            '--git-dir=' + self.git_dir,
            '--work-tree=' + self.git_tree,
            'show-ref',
            '--tags',
            '--abbrev=7'
        ]
        results = self.run_command(args)
        return results

    def git_current_branch(self):
        args = [
            self.settings.git_binary_path,
            '--git-dir=' + self.git_dir,
            '--work-tree=' + self.git_tree,
            'rev-parse',
            '--abbrev-ref',
            'HEAD'
        ]
        result = self.run_command(args)
        return result

    def run_command(self, args):
        # print('run_command: ' + str(args))
        p = Promise()
        def read_output():
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            proc = subprocess.Popen(args, stdout=subprocess.PIPE,
                                    startupinfo=startupinfo, stderr=subprocess.PIPE)
            stdout_output = proc.stdout.read()
            p.updateValue(stdout_output)

        sublime.set_timeout_async(read_output, 0)
        return p