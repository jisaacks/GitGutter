import os

import sublime

try:
    from .git_gutter_settings import settings
except (ImportError, ValueError):
    from git_gutter_settings import settings

ST3 = int(sublime.version()) >= 3000


class GitGutterShowDiff(object):
    region_names = ['deleted_top', 'deleted_bottom',
                    'deleted_dual', 'inserted', 'changed',
                    'untracked', 'ignored']

    def __init__(self, view, git_handler):
        """Initialize an object instance."""
        self.view = view
        self.git_handler = git_handler
        self.diff_results = None
        self.show_untracked = False
        self.file_state = 'committed'

    def run(self):
        """API entry point."""

        # git_time_reset was called recently, maybe branch has changed
        # Status message needs an update on this run.
        if self.git_handler.git_time_cleared():
            self.diff_results = None
        self.git_handler.diff().then(self._check_ignored_or_untracked)

    def _check_ignored_or_untracked(self, contents):
        """Check diff result and invoke gutter and status message update.

        Arguments:
            contents - a tuble of ([inserted], [modified], [deleted]) lines
        """
        if self.git_handler.in_repo() is False:
            show_untracked = settings.get(
                'show_markers_on_untracked_file', False)
            # need to check for ignored or untracked file
            if show_untracked:
                def bind_ignored_or_untracked(is_ignored):
                    if is_ignored:
                        self._bind_files('ignored')
                    else:
                        def bind_untracked(is_untracked):
                            if is_untracked:
                                self._bind_files('untracked')
                            else:
                                # file was staged but empty
                                self._bind_files('inserted')
                        self.git_handler.untracked().then(bind_untracked)
                self.git_handler.ignored().then(bind_ignored_or_untracked)

            # show_untracked was set to false recently so clear gutter
            elif self.show_untracked:
                # must differ from 'untracked'
                self.file_state = 'not tracked'
                self._clear_regions()
                self._update_status(([], [], []))
            self.show_untracked = show_untracked

        # update the if lines modified
        elif self.diff_results is None or self.diff_results != contents:
            self.diff_results = contents
            self._update_regions(contents)
            self._update_status(contents)

    def _update_regions(self, contents):
        """Update gutter icons for modified files.

        Arguments:
            contents - a tuble of ([inserted], [modified], [deleted]) lines
        """
        inserted, modified, deleted = contents
        self._clear_all()
        if inserted or modified or deleted:
            self.file_state = 'modified'
            self._lines_removed(deleted)
            self._bind_icons('inserted', inserted)
            self._bind_icons('changed', modified)
        else:
            self.file_state = 'commited'

    def _update_status(self, contents):
        """Update status message.

        Arguments:
            contents - a tuble of ([inserted], [modified], [deleted]) lines
        """
        if settings.show_status != 'none':
            def set_status(branch_name):
                inserted = len(contents[0])
                modified = len(contents[1])
                deleted = len(contents[2])
                self._set_status(
                    inserted, modified, deleted,
                    self.git_handler.format_compare_against(),
                    branch_name,
                    self.file_state)
            if settings.show_status == 'all':
                self.git_handler.git_current_branch().then(set_status)
            else:
                set_status('')
        else:
            self._set_status(0, 0, 0, '', '', '')

    def _set_status(self, inserted, modified, deleted, compare, branch, state):
        """Built and print the updated status message.

        Arguments:
            inserted    - inserted lines count
            modified    - modified lines count
            deleted     - deleted lines count
            compare     - HEAD or commit name
            branch      - branch name
            state       - the state of the whole file
                          (committed/modified/ignored/untracked)
        """
        set_status = self.view.set_status
        # print the checked out branch
        set_status('git_gutter_1_branch',
                   'On : ' + branch if branch else '')
        # print the branch/tag/commit this file is compared against
        set_status('git_gutter_2_comparison',
                   'Comparing against : ' + compare if compare else '')
        # print the open file's state
        set_status('git_gutter_3_filestate',
                   'File is ' + state if state else '')
        # print deleted regions statistic
        if deleted:
            message = 'Deleted : %d region' % deleted
            if deleted > 1:
                message += 's'
        else:
            message = ''
        set_status('git_gutter_4_deleted', message)
        # print inserted regions statistic
        if inserted:
            message = 'Inserted : %d line' % inserted
            if inserted > 1:
                message += 's'
        else:
            message = ''
        set_status('git_gutter_5_inserted', message)
        # print modified regions statistic
        if modified:
            message = 'Modified : %d' % modified
            if inserted + deleted == 0:
                message += ' line'
                if modified > 1:
                    message += 's'
        else:
            message = ''
        set_status('git_gutter_6_modified', message)

    def _clear_all(self):
        for region_name in self.region_names:
            self.view.erase_regions('git_gutter_%s' % region_name)

    def _is_region_protected(self, region):
        # Load protected Regions from Settings
        protected_regions = settings.get('protected_regions', [])
        # List of Lists of Regions
        sets = [self.view.get_regions(r) for r in protected_regions]
        # List of Regions
        regions = [r for rs in sets for r in rs]
        # get the line of the region (gutter icon applies to whole line)
        region_line = self.view.line(region)
        for r in regions:
            if r.contains(region) or region_line.contains(r):
                return True

        return False

    def _lines_to_regions(self, lines):
        regions = []
        for line in lines:
            position = self.view.text_point(line - 1, 0)
            region = sublime.Region(position, position + 1)
            if not self._is_region_protected(region):
                regions.append(region)
        return regions

    def _lines_removed(self, lines):
        top_lines = lines
        bottom_lines = [line - 1 for line in lines if line > 1]
        dual_lines = []
        for line in top_lines:
            if line in bottom_lines:
                dual_lines.append(line)
        for line in dual_lines:
            bottom_lines.remove(line)
            top_lines.remove(line)

        self._bind_icons('deleted_top', top_lines)
        self._bind_icons('deleted_bottom', bottom_lines)
        self._bind_icons('deleted_dual', dual_lines)

    def _plugin_dir(self):
        path = os.path.realpath(__file__)
        root = os.path.split(os.path.dirname(path))[1]
        return os.path.splitext(root)[0]

    def _icon_path(self, icon_name):
        if icon_name in ['deleted_top', 'deleted_bottom', 'deleted_dual']:
            if self.view.line_height() > 15:
                icon_name = icon_name + "_arrow"

        if int(sublime.version()) < 3014:
            path = '../GitGutter'
            extn = ''
        else:
            path = 'Packages/' + self._plugin_dir()
            extn = '.png'

        return "/".join([path, 'icons', icon_name + extn])

    def _bind_icons(self, event, lines):
        regions = self._lines_to_regions(lines)
        event_scope = event
        if event.startswith('deleted'):
            event_scope = 'deleted'
        scope = 'markup.%s.git_gutter' % event_scope
        icon = self._icon_path(event)
        if ST3 and settings.show_in_minimap:
            flags = sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE
        else:
            flags = sublime.HIDDEN
        self.view.add_regions(
            'git_gutter_%s' % event, regions, scope, icon, flags)

    def _bind_files(self, event):
        """Add gutter icons to each line in the view.

        Arguments:
            event   - is one of REGION_NAMES
        """
        self.file_state = event
        lines = [line + 1 for line in range(self._total_lines())]
        self._bind_icons(event, lines)
        self._update_status(([], [], []))

    def _total_lines(self):
        chars = self.view.size()
        region = sublime.Region(0, chars)
        lines = self.view.lines(region)
        return len(lines)
