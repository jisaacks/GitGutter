import os
import subprocess
import re
import codecs

import sublime

try:
    from . import git_helper
    from .git_gutter_settings import settings
    from .view_collection import ViewCollection
except (ImportError, ValueError):
    import git_helper
    from git_gutter_settings import settings
    from view_collection import ViewCollection


class GitGutterHandler:
    def __init__(self, view):
        self.view = view

        self.git_temp_file = ViewCollection.git_tmp_file(self.view)
        self.buf_temp_file = ViewCollection.buf_tmp_file(self.view)
        self.git_tree = None
        self.git_dir = None
        self.git_path = None

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

        with open(self.buf_temp_file, 'wb') as f:
            if self.view.encoding() == "UTF-8 with BOM":
                f.write(codecs.BOM_UTF8)

            f.write(contents)

    def update_git_file(self):
        # the git repo won't change that often
        # so we can easily wait 5 seconds
        # between updates for performance
        if ViewCollection.git_time(self.view) > 5:
            with open(self.git_temp_file, 'w'):
                pass

            args = [
                settings.git_binary_path,
                '--git-dir=' + self.git_dir,
                '--work-tree=' + self.git_tree,
                'show',
                ViewCollection.get_compare(self.view) + ':' + self.git_path,
            ]
            try:
                contents = self.run_command(args)
                contents = contents.replace(b'\r\n', b'\n')
                contents = contents.replace(b'\r', b'\n')
                with open(self.git_temp_file, 'wb') as f:
                    f.write(contents)

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
        return (inserted, modified, deleted)

    def diff_str(self):
        if self.on_disk() and self.git_path:
            self.update_git_file()
            self.update_buf_file()
            args = [
                settings.git_binary_path,
                'diff', '-U0', '--no-color', '--no-index',
                settings.ignore_whitespace,
                settings.patience_switch,
                self.git_temp_file,
                self.buf_temp_file,
            ]
            args = list(filter(None, args))  # Remove empty args
            results = self.run_command(args)
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
            return decoded_results
        else:
            return ""

    def process_diff_line_change(self, diff_str, line_nr):
        hunk_re = '^@@ \-(\d+),?(\d*) \+(\d+),?(\d*) @@'
        hunks = re.finditer(hunk_re, diff_str, re.MULTILINE)

        # we also want to extract the position of the surrounding changes
        first_change = prev_change = next_change = None

        for hunk in hunks:
            start = int(hunk.group(3))
            size = int(hunk.group(4) or 1)
            if first_change is None:
                first_change = start
            # special handling to also match the line below deleted
            # content
            if size == 0 and line_nr == start + 1:
                pass
            # continue if the hunk is before the line
            elif start + size < line_nr:
                prev_change = start
                continue
            # break if the hunk is after the line
            elif line_nr < start:
                break
            # in the following the line is inside the hunk
            try:
                next_hunk = next(hunks)
                hunk_end = next_hunk.start()
                next_change = int(next_hunk.group(3))
            except:
                hunk_end = len(diff_str)
            # extract the content of the hunk
            hunk_content = diff_str[hunk.start():hunk_end]
            # store all deleted lines (starting with -)
            lines = [line[1:] for line in hunk_content.split("\n")[1:]
                     if line.startswith("-")]

            # if wrap is disable avoid wrapping
            wrap = settings.get('next_prev_change_wrap', True)
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
            meta = {
                "first_change": first_change,
                "next_change": next_change,
                "prev_change": prev_change
            }
            return lines, start, size, meta
        return [], -1, -1, {}

    def diff_line_change(self, line):
        diff_str = self.diff_str()
        return self.process_diff_line_change(diff_str, line)

    def diff(self):
        diff_str = self.diff_str()
        if diff_str:
            return self.process_diff(diff_str)
        else:
            return ([], [], [])

    def untracked(self):
        return self.handle_files([])

    def ignored(self):
        return self.handle_files(['-i'])

    def handle_files(self, additionnal_args):
        if self.on_disk() and self.git_path:
            args = [
                settings.git_binary_path,
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

    def git_commits(self):
        args = [
            settings.git_binary_path,
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
            settings.git_binary_path,
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
            settings.git_binary_path,
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
            settings.git_binary_path,
            '--git-dir=' + self.git_dir,
            '--work-tree=' + self.git_tree,
            'rev-parse',
            '--abbrev-ref',
            'HEAD'
        ]
        result = self.run_command(args)
        return result

    def run_command(self, args):
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        proc = subprocess.Popen(args, stdout=subprocess.PIPE,
                                startupinfo=startupinfo, stderr=subprocess.PIPE)
        return proc.stdout.read()
