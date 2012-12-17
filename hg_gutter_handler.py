import os
import sublime
import subprocess
import re
import vcs_helpers
from view_collection import ViewCollection


class HgGutterHandler:
    def __init__(self, view):
        self.view = view
        self.hg_temp_file = ViewCollection.git_tmp_file(self.view)
        self.buf_temp_file = ViewCollection.buf_tmp_file(self.view)

        vcs_helper = vcs_helpers.HgHelper()
        if self.on_disk():
            self.hg_tree = vcs_helper.vcs_tree(self.view)
            self.hg_dir = vcs_helper.vcs_dir(self.hg_tree)
            self.hg_path = vcs_helper.vcs_file_path(self.view, self.hg_tree)

    def on_disk(self):
        # if the view is saved to disk
        return self.view.file_name() is not None

    def reset(self):
        if self.on_disk() and self.hg_path:
            self.view.run_command('git_gutter')

    def get_hg_path(self):
        return self.hg_path

    def update_buf_file(self):
        chars = self.view.size()
        region = sublime.Region(0, chars)
        contents = self.view.substr(region).encode('utf-8')
        contents = contents.replace('\r\n', '\n')
        contents = contents.replace('\r', '\n')
        f = open(self.buf_temp_file.name, 'w')
        f.write(contents)
        f.close()

    def update_hg_file(self):
        # the hg repo won't change that often
        # so we can easily wait 5 seconds
        # between updates for performance
        if ViewCollection.git_time(self.view) > 5:
            open(self.hg_temp_file.name, 'w').close()
            args = [
                'hg',
                '--repository',
                self.hg_tree,
                'cat',
                os.path.join(self.hg_tree, self.hg_path),
            ]
            try:
                contents = self.run_command(args)
                contents = contents.replace('\r\n', '\n')
                contents = contents.replace('\r', '\n')
                f = open(self.hg_temp_file.name, 'w')
                f.write(contents)
                f.close()
                ViewCollection.update_hg_time(self.view)
            except Exception:
                pass

    def total_lines(self):
        chars = self.view.size()
        region = sublime.Region(0, chars)
        lines = self.view.lines(region)
        lines_count = len(lines)
        return range(1, lines_count + 1)

    def process_diff(self, diff_str):
        inserted = []
        modified = []
        deleted = []
        pattern = re.compile(r'(\d+),?(\d*)(.)(\d+),?(\d*)')
        lines = diff_str.splitlines()
        for line in lines:
            m = pattern.match(line)
            if not m:
                continue
            kind = m.group(3)
            line_start = int(m.group(4))
            if len(m.group(5)) > 0:
                line_end = int(m.group(5))
            else:
                line_end = line_start
            if kind == 'c':
                modified += range(line_start, line_end + 1)
            elif kind == 'a':
                inserted += range(line_start, line_end + 1)
            elif kind == 'd':
                if line == 1:
                    deleted.append(line_start)
                else:
                    deleted.append(line_start + 1)
        if inserted == self.total_lines():
            # All lines are "inserted"
            # this means this file is either:
            # - New and not being tracked *yet*
            # - Or it is a *hgignored* file
            return ([], [], [])
        else:
            return (inserted, modified, deleted)

    def diff(self):
        if self.on_disk() and self.hg_path:
            self.update_hg_file()
            self.update_buf_file()
            args = [
                'diff',
                self.hg_temp_file.name,
                self.buf_temp_file.name,
            ]
            results = self.run_command(args)
            return self.process_diff(results)
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
