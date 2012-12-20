import git_helper
import os
import sublime
import subprocess
import re
import threading
from view_collection import ViewCollection
from git_gutter import GitGutter


class GitGutterHandler:
    def __init__(self, view):
        self.view = view
        self.git_temp_file = ViewCollection.git_tmp_file(self.view)
        self.buf_temp_file = ViewCollection.buf_tmp_file(self.view)
        if self.on_disk():
            self.git_tree = git_helper.git_tree(self.view)
            self.git_dir = git_helper.git_dir(self.git_tree)
            self.git_path = git_helper.git_file_path(self.view, self.git_tree)

    def on_disk(self):
        # if the view is saved to disk
        return self.view.file_name() is not None

    def reset(self):
        if self.on_disk() and self.git_path:
            GitGutter(self.view).run()

    def get_git_path(self):
        return self.git_path

    def update_buf_file(self):
        chars = self.view.size()
        region = sublime.Region(0, chars)
        contents = self.view.substr(region).encode('utf-8')
        contents = contents.replace('\r\n', '\n')
        contents = contents.replace('\r', '\n')
        f = open(self.buf_temp_file.name, 'w')
        f.write(contents)
        f.close()

    def update_git_file(self, callback):
        def write_git_file(contents):
            try:
                contents = contents.replace('\r\n', '\n')
                contents = contents.replace('\r', '\n')
                f = open(self.git_temp_file.name, 'w')
                f.write(contents)
                f.close()
                ViewCollection.update_git_time(self.view)
                callback()
            except Exception:
                pass

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
            self.run_command(args, write_git_file)
        else:
            callback()

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
            # - Or it is a *gitignored* file
            return ([], [], [])
        else:
            return (inserted, modified, deleted)

    def diff(self, callback):
        def exec_diff():
            args = [
                'diff',
                self.git_temp_file.name,
                self.buf_temp_file.name,
            ]
            results = self.run_command(args,
                lambda results: callback(self.process_diff(results)))

        if self.on_disk() and self.git_path:
            self.update_buf_file()
            self.update_git_file(exec_diff)
        else:
            callback([], [], [])

    def run_command(self, args, callback):
        AsyncCommand(args, callback).start()


class AsyncCommand(threading.Thread):
    def __init__(self, args, callback):
        self.args = args
        self.callback = callback
        threading.Thread.__init__(self)

    def run(self):
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        proc = subprocess.Popen(self.args, stdout=subprocess.PIPE,
            startupinfo=startupinfo)
        stdout = proc.stdout.read()
        sublime.set_timeout(lambda: self.callback(stdout), 1)
