import sublime
import sublime_plugin
try:
    from GitGutter.view_collection import ViewCollection
except ImportError:
    from view_collection import ViewCollection


def plugin_loaded():
    """
    Ugly hack for icons in ST3
    kudos:
    github.com/facelessuser/BracketHighlighter/blob/BH2ST3/bh_core.py#L1380
    """
    from os import makedirs
    from os.path import exists, join

    icon_path = join(sublime.packages_path(), "Theme - Default")
    if not exists(icon_path):
        makedirs(icon_path)


class GitGutterCommand(sublime_plugin.WindowCommand):
    region_names = ['deleted_top', 'deleted_bottom',
                    'deleted_dual', 'inserted', 'changed',
                    'untracked', 'ignored']

    qualifiers = ['staged','unstaged','staged_unstaged']

    def run(self, force_refresh=False):
        self.view = self.window.active_view()
        if not self.view:
            # View is not ready yet, try again later.
            sublime.set_timeout(self.run, 1)
            return
        self.clear_all()
        if ViewCollection.untracked(self.view):
            self.bind_files('untracked')
        elif ViewCollection.ignored(self.view):
            self.bind_files('ignored')
        else:
            if force_refresh:
                ViewCollection.clear_times(self.view)
            
            staged = ViewCollection.has_stages(self.view)
            if staged:
                # Mark changes qualified with staged/unstaged/staged_unstaged
                
                # Get unstaged changes
                u_inserted, u_modified, u_deleted = self.unstaged_changes()
                
                # Get staged changes
                s_inserted, s_modified, s_deleted = self.staged_changes()
                
                # Find lines with a mix of staged/unstaged
                # (only necessary for modified)
                m_modified = self.mixed_mofified(u_modified,
                    [s_inserted, s_modified, s_deleted])

                # Remove mixed from unstaged
                u_inserted = self.list_subtract(u_inserted, m_modified)
                u_modified = self.list_subtract(u_modified, m_modified)
                u_deleted  = self.list_subtract(u_deleted, m_modified)

                # Remove mixed from staged
                s_inserted = self.list_subtract(s_inserted, m_modified)
                s_modified = self.list_subtract(s_modified, m_modified)
                s_deleted  = self.list_subtract(s_deleted, m_modified) 

                # Unstaged
                self.lines_removed(u_deleted, 'unstaged')
                self.bind_icons('inserted', u_inserted, 'unstaged')
                self.bind_icons('changed', u_modified, 'unstaged')

                # Staged
                self.lines_removed(s_deleted, 'staged')
                self.bind_icons('inserted', s_inserted, 'staged')
                self.bind_icons('changed', s_modified, 'staged')

                # Mixed
                self.bind_icons('changed', m_modified, 'staged_unstaged') 
            else:
                # Mark changes without a qualifier
                inserted, modified, deleted = self.all_changes()

                self.lines_removed(deleted)
                self.bind_icons('inserted', inserted)
                self.bind_icons('changed', modified)

    def all_changes(self):
        return ViewCollection.diff(self.view)

    def unstaged_changes(self):
        return ViewCollection.unstaged(self.view)

    def staged_changes(self):
        return ViewCollection.staged(self.view)

    def list_subtract(self, a, b):
        subtracted = [elem for elem in a if elem not in b]
        return subtracted

    def list_intersection(self, a, b):
        intersected = [elem for elem in a if elem in b]
        return intersected

    def mixed_mofified(self, a, lists):
        # a is a list of modified lines
        # lists is a list of lists (inserted, modified, deleted)
        # We want the values in a that are in any of the lists
        c = []
        for b in lists:
            mix = self.list_intersection(a,b)
            [c.append(elem) for elem in mix]
        return c

    def clear_all(self):
        for region_name in self.region_names:
            self.view.erase_regions('git_gutter_%s' % region_name)
            for qualifier in self.qualifiers:
                self.view.erase_regions('git_gutter_%s_%s' % (
                    region_name, qualifier))

    def lines_to_regions(self, lines):
        regions = []
        for line in lines:
            position = self.view.text_point(line - 1, 0)
            region = sublime.Region(position, position)
            regions.append(region)
        return regions

    def lines_removed(self, lines, qualifier=None):
        top_lines = lines
        bottom_lines = [line - 1 for line in lines if line > 1]
        dual_lines = []
        for line in top_lines:
            if line in bottom_lines:
                dual_lines.append(line)
        for line in dual_lines:
            bottom_lines.remove(line)
            top_lines.remove(line)

        self.bind_icons('deleted_top', top_lines, qualifier)
        self.bind_icons('deleted_bottom', bottom_lines, qualifier)
        self.bind_icons('deleted_dual', dual_lines, qualifier)

    def icon_path(self, icon_name):
        if icon_name in ['deleted_top','deleted_bottom','deleted_dual']:
            if self.view.line_height() > 15:
                icon_name = icon_name + "_arrow"

        if int(sublime.version()) < 3014:
            path = '..'
            extn = ''
        else:
            path = 'Packages'
            extn = '.png'
        
        return path + '/GitGutter/icons/' + icon_name + extn

    def icon_scope(self, event_scope, qualifier):
        scope = 'markup.%s.git_gutter' % event_scope
        if qualifier:
            scope += "." + qualifier
        return scope

    def icon_region(self, event, qualifier):
        region = 'git_gutter_%s' % event
        if qualifier:
            region += "_" + qualifier
        return region

    def bind_icons(self, event, lines, qualifier=None):
        regions = self.lines_to_regions(lines)
        event_scope = event
        if event.startswith('deleted'):
            event_scope = 'deleted'
        if qualifier == "staged_unstaged":
            icon_name = "staged_unstaged"
        else:
            icon_name = event
        scope = self.icon_scope(event_scope,qualifier)
        icon = self.icon_path(icon_name)
        key = self.icon_region(event,qualifier)
        self.view.add_regions(key, regions, scope, icon)

    def bind_files(self, event):
        lines = []
        lineCount = ViewCollection.total_lines(self.view)
        i = 0
        while i < lineCount:
            lines += [i + 1]
            i = i + 1
        self.bind_icons(event, lines)
