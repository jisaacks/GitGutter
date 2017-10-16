# -*- coding: utf-8 -*-
try:
    # avoid exceptions if dependency is not yet satisfied
    import jinja2.environment
    _HAVE_JINJA2 = True
except ImportError:
    _HAVE_JINJA2 = False

import sublime

_ICON_EXT = '.png' if int(sublime.version()) >= 3000 else ''


class GitGutterShowDiff(object):
    region_names = ('deleted_top', 'deleted_bottom', 'deleted_dual',
                    'inserted', 'changed', 'untracked', 'ignored')

    def __init__(self, git_handler):
        """Initialize GitGutterShowDiff object."""
        self.git_handler = git_handler
        self._line_height = 0
        self._minimap_size = 1
        # True if diff is running
        self._busy = False

    def __del__(self):
        """Delete GitGutterShowDiff object.

        Clear all output to prevent zombies if the plugin is disabled.
        """
        self.clear()

    def clear(self):
        """Remove all gutter icons and status messages."""
        self.git_handler.view.erase_status('00_git_gutter')
        self._clear_regions()

    def run(self):
        """Run diff and update gutter icons and status message."""
        if not self._busy:
            self._busy = True
            self.git_handler.diff().then(self._check_ignored_or_untracked)

    def _check_ignored_or_untracked(self, contents):
        """Check diff result and invoke gutter and status message update.

        Arguments:
            contents (tuble): The result of git_handler.diff(), with the
                information about the modifications of the file.
                Scheme: (first, last, [inserted], [modified], [deleted])
        """
        # nothing to update
        if contents is None:
            self._busy = False
            return

        if not self.git_handler.in_repo():
            show_untracked = self.git_handler.settings.get(
                'show_markers_on_untracked_file', False)

            def bind_ignored_or_untracked(is_ignored):
                if is_ignored:
                    event = 'ignored'
                    self._update_status(event, (0, 0, [], [], []))
                    if show_untracked:
                        self._bind_files(event)
                else:
                    def bind_untracked(is_untracked):
                        event = 'untracked' if is_untracked else 'inserted'
                        self._update_status(event, (0, 0, [], [], []))
                        if show_untracked:
                            self._bind_files(event)
                    self.git_handler.untracked().then(bind_untracked)
            self.git_handler.ignored().then(bind_ignored_or_untracked)
        else:
            self._update_ui(contents)

    def _update_ui(self, contents):
        """Update gutter icons for modified files.

        Arguments:
            contents (tuble): The result of git_handler.diff(), with the
                information about the modifications of the file.
                Scheme: (first, last, [inserted], [modified], [deleted])
        """
        try:
            view = self.git_handler.view
            self._line_height = view.line_height()
            self._minimap_size = self.git_handler.settings.show_in_minimap
            regions = self._contents_to_regions(contents)
            if not self.git_handler.view_file_changed():
                for name, region in zip(self.region_names, regions):
                    self._bind_regions(name, region)
            self._update_status(
                'modified' if contents[0] else 'committed', contents)
        except IndexError:
            # Fail silently and don't update ui if _content_to_regions raises
            # index error as the result wouldn't be valid anyway.
            pass
        finally:
            self._busy = False

    def _update_status(self, file_state, contents):
        """Update status message.

        The method joins and renders the lines read from 'status_bar_text'
        setting to the status bar using the jinja2 library to fill in all
        the state information of the open file.

        Arguments:
            file_state (string): The git status of the open file.
            contents (tuble): The result of git_handler.diff(), with the
                information about the modifications of the file.
                Scheme: (first, last, [inserted], [modified], [deleted])
        """
        if not self.git_handler.settings.get('show_status_bar_text', False):
            self.git_handler.view.erase_status('00_git_gutter')
            return

        # Update status bar only for active view
        window = self.git_handler.view.window()
        if window and window.active_view().id() != self.git_handler.view.id():
            return

        def set_status(branch_status):
            _, _, inserted, modified, deleted = contents
            template = (
                self.git_handler.settings.get('status_bar_text')
                if _HAVE_JINJA2 else None
            )
            if template:
                # render the template using jinja2 library
                text = jinja2.environment.Template(''.join(template)).render(
                    repo=self.git_handler.repository_name,
                    compare=self.git_handler.format_compare_against(),
                    state=file_state, deleted=len(deleted),
                    inserted=len(inserted), modified=len(modified),
                    **branch_status)
            else:
                # Render hardcoded text if jinja is not available.
                parts = []
                parts.append('On %s' % branch_status['branch'])
                compare = self.git_handler.format_compare_against()
                if compare not in ('HEAD', branch_status['branch']):
                    parts.append('Comparing against %s' % compare)
                count = len(inserted)
                if count:
                    parts.append('%d+' % count)
                count = len(deleted)
                if count:
                    parts.append('%d-' % count)
                count = len(modified)
                if count:
                    parts.append(u'%d≠' % count)
                text = ', '.join(parts)
            # add text and try to be the left most one
            self.git_handler.view.set_status('00_git_gutter', text)

        self.git_handler.git_branch_status().then(set_status)

    def _contents_to_regions(self, contents):
        """Convert the diff contents to gutter regions.

        The returned tuple has the same format as `region_names`.

        As a line can hold only on gutter icon the 'deleted' lines are split
        into three different regions depending on the surrounding line states,
        first. All other lines are mapped normally.

        Arguments:
            contents (tuple): The result of git_handler.diff(), with the
                information about the modifications of the file.
                Scheme: (first, last, [inserted], [modified], [deleted])
        """
        first_line, last_line, ins_lines, mod_lines, del_lines = contents
        # Return empty regions, if diff result is empty
        if first_line == 0:
            return ([], [], [], [], [], [], [])
        # initiate the lines to regions map
        lines_regions = self._get_modified_region(first_line, last_line)
        protected = self._get_protected_regions()
        return (
            # deleted regions
            self._deleted_lines_to_regions(
                first_line, del_lines, lines_regions, protected) +
            # inserted regions
            [self._lines_to_regions(
                first_line, ins_lines, lines_regions, protected)] +
            # modified regions
            [self._lines_to_regions(
                first_line, mod_lines, lines_regions, protected)] +
            # untracked / ignored regions
            [] + [])

    def _get_modified_region(self, first_line, last_line):
        """Create a list of all line start points in the modified Region.

        A modified region contains all lines from the first found diff up to
        the last one.

        Note:
            The points are calculated directly on the buffer string as
            view.lines(...) takes up to 3 times longer, what hurts especially
            with larger files.

        Arguments:
            first_line(int): The line to start reading with
            last_line(int): The line to stop reading with

        Returns:
            list: The list of text positions of each line start
        """
        view = self.git_handler.view
        start = view.text_point(first_line - 1, 0)
        end = view.text_point(last_line, 0)
        region = sublime.Region(start, end)
        lines = [start]
        for line in view.substr(region).splitlines():
            start += len(line) + 1
            lines.append(start)
        # Add one more dummy line to avoid IndexError due to deleted_bottom
        # regions at the end of file.
        lines.append(start + 1)
        return lines

    def _get_protected_regions(self):
        """Create a list of line start points of all protected lines.

        A protected region describes a line which is occupied by a higher prior
        gutter icon which must not be overwritten by GitGutter.

        Returns:
            frozenset: A list of protected lines' start points.
        """
        view = self.git_handler.view
        keys = self.git_handler.settings.get('protected_regions', [])
        return frozenset(
            view.line(reg).a for key in keys for reg in view.get_regions(key))

    def _deleted_lines_to_regions(self, first_line, lines, lines_regions, protected):
        """Convert the list of deleted lines' numbers to three deleted regions.

        Arguments:
            first_line (int): The line number hold by lines_region[0]
            lines (list): The list of line numbers to add gutter icons to
            lines_regions(dict): A map used to translate lines to regions
            protected(list): The list of line start points to exclude
        """
        deleted_top, deleted_dual, deleted_bottom = [], [], []
        # convert deleted lines to regions
        if lines:
            bottom_lines = [line - 1 for line in lines if line > 1]
            for line in lines:
                index = line - first_line
                start = lines_regions[index]
                if start not in protected:
                    end = lines_regions[index + 1]
                    region = sublime.Region(
                        start, min(end, start + self._minimap_size))
                    if line in bottom_lines:
                        deleted_dual.append(region)
                        bottom_lines.remove(line)
                    else:
                        deleted_top.append(region)
            deleted_bottom = self._lines_to_regions(
                first_line, bottom_lines, lines_regions, protected)
        return [deleted_top, deleted_bottom, deleted_dual]

    def _lines_to_regions(self, first_line, lines, lines_regions, protected):
        """Convert the list of line numbers to regions.

        Arguments:
            first_line (int): The line number hold by lines_region[0]
            lines (list): The list of line numbers to add gutter icons to
            lines_regions(dict): A map used to translate lines to regions
            protected(list): The list of line start points to exclude
        """
        regions = []
        for line in lines:
            index = line - first_line
            start = lines_regions[index]
            if start not in protected:
                end = lines_regions[index + 1]
                region = sublime.Region(
                    start, min(end, start + self._minimap_size))
                regions.append(region)
        return regions

    def _bind_files(self, event):
        """Add gutter icons to each line in the view.

        The regions are calculated directly on the buffer string as
        view.lines(...) takes up to 3 times longer, what hurts especially
        with larger files.

        Arguments:
            event (string): The element of self.region_names to bind
        """
        view = self.git_handler.view
        start = 0
        regions = []
        protected = self._get_protected_regions()
        chars = view.size()
        region = sublime.Region(start, chars)
        for line in view.substr(region).splitlines():
            end = start + len(line)
            if start not in protected:
                region = sublime.Region(
                    start, min(end, start + self._minimap_size))
                regions.append(region)
            start = end + 1
        self._line_height = view.line_height()
        self._minimap_size = self.git_handler.settings.show_in_minimap
        self._bind_regions(event, regions)
        self._clear_regions(event)
        self._busy = False

    def _bind_regions(self, event, regions):
        """Add gutter icons to all lines defined by their regions.

        Arguments:
            event (string): The element of self.region_names to bind
            regions(list): A list of sublime.Region objects to add icons to.
        """
        region_name = 'git_gutter_%s' % event
        if regions:
            if event.startswith('del'):
                scope = 'markup.deleted.git_gutter'
            else:
                scope = 'markup.%s.git_gutter' % event
            icon = self._icon_path(event)
            if self._minimap_size:
                flags = sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE
            else:
                flags = sublime.HIDDEN
            self.git_handler.view.add_regions(
                region_name, regions, scope, icon, flags)
        else:
            self.git_handler.view.erase_regions(region_name)

    def _clear_regions(self, exclude=[]):
        """Remove all gutter icons.

        Arguments:
            exclude (string): The self.region_name not to clear.
        """
        for name in self.region_names:
            if name not in exclude:
                self.git_handler.view.erase_regions('git_gutter_%s' % name)

    def _icon_path(self, event):
        """Built the full path to the icon to show for the event.

        Arguments:
            event (string): The element of self.region_names to bind
        """
        if self._line_height > 16 and event.startswith('del'):
            arrow = '_arrow'
        else:
            arrow = ''
        return ''.join((
            self.git_handler.settings.theme_path, '/',
            event, arrow, _ICON_EXT))
