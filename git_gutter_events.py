import time

import sublime
import sublime_plugin

try:
    from .git_gutter_settings import settings
except (ImportError, ValueError):
    from git_gutter_settings import settings

ST3 = int(sublime.version()) >= 3000


def async_event_listener(EventListener):
    if ST3:
        async_methods = set([
            'on_new',
            'on_clone',
            'on_load',
            'on_pre_save',
            'on_post_save',
            'on_modified',
            'on_selection_modified',
            'on_activated',
            'on_deactivated',
        ])
        for attr_name in dir(EventListener):
            if attr_name in async_methods:
                attr = getattr(EventListener, attr_name)
                setattr(EventListener, attr_name + '_async', attr)
                delattr(EventListener, attr_name)
    return EventListener


@async_event_listener
class GitGutterEvents(sublime_plugin.EventListener):
    def __init__(self):
        self.latest_keypresses = {}

    # Synchronous

    def on_modified(self, view):
        """Run git_gutter for visible view.

        The on_modified() is called when typing into an active view
        and might be called for inactive views if the file changes on disk.

        If the view is not visible, git_gutter will be triggered
        by on_activate() later. So it's useless here.
        """
        if self.live_mode() and self.is_view_visible(view):
            self.debounce(view, 'modified')

    def on_clone(self, view):
        self.debounce(view, 'clone')

    def on_post_save(self, view):
        """Run git_gutter after saving.

        If the view is not visible git_gutter does not run with
        live_mode or focus_change_mode enabled as they would trigger
        git_gutter with the next on_activate() event.
        """
        if not self.change_mode() or self.is_view_visible(view):
            self.debounce(view, 'post-save')

    def on_activated(self, view):
        """Run git_gutter when the view is activated.

        This event is also called after a file is opened into an
        active view.
        """
        if self.change_mode():
            self.debounce(view, 'activated')

    def on_hover(self, view, point, hover_zone):
        if hover_zone != sublime.HOVER_GUTTER:
            return
        # don't let the popup flicker / fight with other packages
        if view.is_popup_visible():
            return
        if not settings.get("enable_hover_diff_popup"):
            return
        view.run_command(
            'git_gutter_diff_popup',
            args={'point': point, 'flags': sublime.HIDE_ON_MOUSE_MOVE_AWAY})

    # Asynchronous

    def debounce(self, view, event_type):
        key = (event_type, view.file_name())
        this_keypress = time.time()
        self.latest_keypresses[key] = this_keypress

        def callback():
            latest_keypress = self.latest_keypresses.get(key, None)
            if this_keypress == latest_keypress:
                view.run_command('git_gutter')

        if ST3:
            set_timeout = sublime.set_timeout_async
        else:
            set_timeout = sublime.set_timeout

        set_timeout(callback, settings.get("debounce_delay"))

    # Settings

    def live_mode(self, default=True):
        return settings.get('live_mode', default)

    def focus_change_mode(self, default=True):
        return settings.get('focus_change_mode', default)

    def change_mode(self):
        return self.live_mode() or self.focus_change_mode()

    def is_view_visible(self, view):
        """Return true if the view is visible.

        Only an active view of a group is visible.
        Note: this should be part of the View class but it isn't.
        """
        w = view.window()
        return any(view == w.active_view_in_group(g)
                   for g in range(w.num_groups())) if w is not None else False
