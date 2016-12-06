import os

import sublime

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
        self.view = view
        self.git_handler = git_handler
        self.diff_results = None
        self.show_untracked = False

    def run(self):
        self.git_handler.diff().then(self._check_ignored_or_untracked)

    def _check_ignored_or_untracked(self, contents):
        """Check diff result and invoke gutter and status message update.

        Arguments:
            contentes - a tuble of ([inserted], [modified], [deleted]) lines
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
                self._clear_all()
                self._update_status(0, 0, 0, "", "")
            self.show_untracked = show_untracked

        # update the if lines changed
        elif self.diff_results is None or self.diff_results != contents:
            self.diff_results = contents
            self._update_ui(contents)

    def _update_ui(self, contents):
        inserted, modified, deleted = contents
        self._clear_all()
        self._lines_removed(deleted)
        self._bind_icons('inserted', inserted)
        self._bind_icons('changed', modified)

        if settings.show_status != "none":
            def update_status_ui(branch_name):
                self._update_status(
                    len(inserted), len(modified), len(deleted),
                    settings.get_compare_against(
                        self.git_handler.git_dir, self.view),
                    branch_name)

            if settings.show_status == 'all':
                self.git_handler.git_current_branch().then(update_status_ui)
            else:
                update_status_ui('')
        else:
            self._update_status(0, 0, 0, "", "")

    def _update_status(self, inserted, modified, deleted, compare, branch):
        def set_status_if(test, key, message):
            if test:
                self.view.set_status("git_gutter_status_" + key, message)
            else:
                self.view.set_status("git_gutter_status_" + key, "")

        set_status_if(inserted > 0, "inserted", "Inserted : %d" % inserted)
        set_status_if(modified > 0, "modified", "Modified : %d" % modified)
        set_status_if(deleted > 0, "deleted", "Deleted : %d regions" % deleted)
        set_status_if(compare, "comparison", "Comparing against : %s" % compare)
        set_status_if(branch, "branch", "On branch : %s" % branch)

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
        lines = [line + 1 for line in range(self._total_lines())]
        self._bind_icons(event, lines)

    def _total_lines(self):
        chars = self.view.size()
        region = sublime.Region(0, chars)
        lines = self.view.lines(region)
        return len(lines)
