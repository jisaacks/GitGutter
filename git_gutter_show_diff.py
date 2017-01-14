import os
import sublime

try:
    # avoid exceptions if dependency is not yet satisfied
    import jinja2.environment
    _HAVE_JINJA2 = True
except:
    _HAVE_JINJA2 = False

try:
    from .git_gutter_settings import settings
except (ImportError, ValueError):
    from git_gutter_settings import settings

ST3 = int(sublime.version()) >= 3000
_ICON_EXT = '.png' if ST3 else ''


class GitGutterShowDiff(object):
    region_names = ['deleted_top', 'deleted_bottom',
                    'deleted_dual', 'inserted', 'changed',
                    'untracked', 'ignored']

    def __init__(self, view, git_handler):
        """Initialize an object instance."""
        self.view = view
        self.git_handler = git_handler
        self.show_untracked = False

    def clear(self):
        """Remove all gutter icons and status messages."""
        self.view.erase_status('00_git_gutter')
        self._clear_all()

    def run(self):
        """Run diff and update gutter icons and status message."""
        self.git_handler.diff().then(self._check_ignored_or_untracked)

    def _check_ignored_or_untracked(self, contents):
        """Check diff result and invoke gutter and status message update.

        Arguments:
            contents - a tuble of ([inserted], [modified], [deleted]) lines
        """
        # nothing to update
        if contents is None:
            return

        if not self.git_handler.in_repo():
            show_untracked = settings.get(
                'show_markers_on_untracked_file', False)

            def bind_ignored_or_untracked(is_ignored):
                if is_ignored:
                    event = 'ignored'
                    self._update_status(event, ([], [], []))
                    if show_untracked:
                        self._bind_files(event)
                else:
                    def bind_untracked(is_untracked):
                        event = 'untracked' if is_untracked else 'inserted'
                        self._update_status(event, ([], [], []))
                        if show_untracked:
                            self._bind_files(event)
                    self.git_handler.untracked().then(bind_untracked)
            self.git_handler.ignored().then(bind_ignored_or_untracked)
        else:
            self._update_ui(contents)

    def _update_ui(self, contents):
        """Update gutter icons for modified files.

        Arguments:
            contents - a tuble of ([inserted], [modified], [deleted]) lines
        """
        inserted, modified, deleted = contents
        self._clear_all()
        if inserted or modified or deleted:
            self._update_status('modified', contents)
            self._lines_removed(deleted)
            self._bind_icons('inserted', inserted)
            self._bind_icons('changed', modified)
        else:
            self._update_status('commited', contents)

    def _update_status(self, file_state, contents):
        """Update status message.

        The method joins and renders the lines read from 'status_bar_text'
        setting to the status bar using the jinja2 library to fill in all
        the state information of the open file.

        Arguments:
            file_state - the git state of the open file.
            contents   - a tuble of ([inserted], [modified], [deleted]) lines
        """
        if not settings.get('show_status_bar_text', False):
            self.view.erase_status('00_git_gutter')
            return

        def set_status(branch_name):
            inserted, modified, deleted = contents
            template = (
                settings.get('status_bar_text')
                if _HAVE_JINJA2 else None
            )
            if template:
                # render the template using jinja2 library
                text = jinja2.environment.Template(''.join(template)).render(
                    repo=self.git_handler.repository_name,
                    compare=self.git_handler.format_compare_against(),
                    branch=branch_name, state=file_state, deleted=len(deleted),
                    inserted=len(inserted), modified=len(modified))
            else:
                # Render hardcoded text if jinja is not available.
                parts = []
                parts.append('On %s' % branch_name)
                compare = self.git_handler.format_compare_against()
                if compare != 'HEAD':
                    parts.append('Comparing against %s' % compare)
                count = len(inserted)
                if count:
                    parts.append('%d+' % count)
                count = len(deleted)
                if count:
                    parts.append('%d-' % count)
                count = len(modified)
                if count:
                    parts.append('%d*' % count)
                text = ', '.join(parts)
            # add text and try to be the left most one
            self.view.set_status('00_git_gutter', text)

        self.git_handler.git_current_branch().then(set_status)

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

    def _icon_path(self, event):
        """Built the full path to the icon to show for the event.

        Arguments:
            event   - is one of self.region_names
        """
        if self.view.line_height() > 15 and event.startswith('del'):
            arrow = '_arrow'
        else:
            arrow = ''
        return ''.join((settings.theme_path, '/', event, arrow, _ICON_EXT))

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
        self._update_status(event, ([], [], []))
        lines = [line + 1 for line in range(self._total_lines())]
        self._bind_icons(event, lines)

    def _total_lines(self):
        chars = self.view.size()
        region = sublime.Region(0, chars)
        lines = self.view.lines(region)
        return len(lines)
