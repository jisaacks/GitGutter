import os
import sublime
import subprocess
import re

try:
    from GitGutter import git_helper
    from GitGutter.view_collection import ViewCollection
except ImportError:
    import git_helper
    from view_collection import ViewCollection


class GitGutterHandler:
    def __init__(self, view):
        self.view = view
        self.git_temp_file = ViewCollection.git_tmp_file(self.view)
        self.buf_temp_file = ViewCollection.buf_tmp_file(self.view)
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
        encoding = encoding.replace('Windows','cp')
        encoding = encoding.replace('-','_')
        encoding = encoding.replace(' ', '')
        return encoding

    def on_disk(self):
        # if the view is saved to disk
        return self.view.file_name() is not None

    def reset(self):
        if self.on_disk() and self.git_path:
            self.view.window().run_command('git_gutter')

    def get_git_path(self):
        return self.git_path

    def update_buf_file(self):
        chars = self.view.size()
        region = sublime.Region(0, chars)

        # Try conversion
        try:
            contents = self.view.substr(region).encode(self._get_view_encoding())
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

    def update_git_file(self):
        # the git repo won't change that often
        # so we can easily wait 5 seconds
        # between updates for performance
        if ViewCollection.git_time(self.view) > 5:
            open(self.git_temp_file.name, 'w').close()
            args = [
                'git',
                '--git-dir=' + self.git_dir,
                '--work-tree=' + self.git_tree,
                'show',
                'HEAD:' + self.git_path,
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
        if len(inserted) == self.total_lines():
            # All lines are "inserted"
            # this means this file is either:
            # - New and not being tracked *yet*
            # - Or it is a *gitignored* file
            return ([], [], [])
        else:
            return (inserted, modified, deleted)

    def diff(self):
        if self.on_disk() and self.git_path:
            self.update_git_file()
            self.update_buf_file()
            args = [
                'git', 'diff', '-U0',
                self.git_temp_file.name,
                self.buf_temp_file.name,
            ]
            results = self.run_command(args)
            encoding = self.view.encoding()
            try:
                decoded_results = results.decode(encoding.replace(' ', ''))
            except UnicodeError:
                decoded_results = results.decode("utf-8")
            return self.process_diff(decoded_results)
        else:
            return ([], [], [])

    def run_command(self, args):
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        proc = subprocess.Popen(args, stdout=subprocess.PIPE,
            startupinfo=startupinfo)
        return proc.stdout.read()
