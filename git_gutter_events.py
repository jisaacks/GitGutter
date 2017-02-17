import time

import sublime
from sublime_plugin import EventListener

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
class GitGutterEvents(EventListener):
    def __init__(self):
        self._latest_keypresses = {}

    # Synchronous

    def on_load(self, view):
        """Run git_gutter after loading, if view is valid.

        Sublime Text marks views as scratch as long as a file is loading,
        but already triggeres the `on_activate()`, which will be therefore
        ignored. The `on_load()` is triggered as soon as the file was loaded.
        If the `git_gutter_enabled` flag was not yet set run `git_gutter`
        to check if the view shows a valid file now.
        """
        if not view.settings().get('git_gutter_enabled', False):
            self.debounce(view, 'load')

    def on_modified(self, view):
        """Run git_gutter for visible view.

        The `on_modified()` is called when typing into an active view and
        might be called for inactive views if the file changes on disk.

        If the view is not visible, git_gutter will be triggered
        by `on_activate()` later. So it's useless here.
        """
        if self.live_mode() and self.is_view_visible(view):
            self.debounce(view, 'modified')

    def on_clone(self, view):
        self.debounce(view, 'clone')

    def on_post_save(self, view):
        """Run git_gutter after saving.

        If the view is not visible git_gutter does not run with
        `live_mode` or `focus_change_mode` enabled as they would trigger
        git_gutter with the next `on_activate()` event.
        """
        if self.is_view_visible(view) or (
                not self.live_mode() and not self.focus_change_mode()):
            self.debounce(view, 'post-save')

    def on_activated(self, view):
        """Run git_gutter when the view is activated.

        When opening larger files, this event is received before `on_load()`
        event and content is not yet fully available. So drop the event if
        the view is still loading or marked as scratch.
        """
        if view.is_scratch() or view.is_loading():
            return

        if self.live_mode() or self.focus_change_mode():
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
        self._latest_keypresses[key] = this_keypress

        def callback():
            latest_keypress = self._latest_keypresses.get(key, None)
            if this_keypress == latest_keypress:
                view.run_command('git_gutter', {'event_type': [event_type]})

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

    def is_view_visible(self, view):
        """Return true if the view is visible.

        Only an active view of a group is visible.
        """
        window = view.window()
        if window:
            view_id = view.id()
            for group in range(window.num_groups()):
                active_view = window.active_view_in_group(group)
                if active_view and active_view.id() == view_id:
                    return True
        return False
