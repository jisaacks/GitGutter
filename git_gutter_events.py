from time import time

import sublime
from sublime_plugin import EventListener

try:
    from .git_gutter_settings import settings
except (ImportError, ValueError):
    from git_gutter_settings import settings


class GitGutterEvents(EventListener):
    """The EventListener invokes evaluation of changes on certain events.

    GitGutter mainly operates in the background by listening to events sent
    from Sublime Text. This event listener is the interface to get informed
    about user interaction to decide when to invoke an evaluation of changes
    by calling the main `git_gutter` command.
    """

    def __init__(self):
        """Initialize GitGutterEvents object."""
        self._latest_events = {}
        self.set_timeout = sublime.set_timeout_async if hasattr(
            sublime, "set_timeout_async") else sublime.set_timeout

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

    def on_close(self, view):
        """Clean up the debounce dictinary."""
        key = view.id()
        if key in self._latest_events:
            del(self._latest_events[key])

    def on_modified(self, view):
        """Run git_gutter for modified visible view.

        The `on_modified()` is called when typing into an active view
        and might be called for inactive views if the file changes on disk.

        If the view is not visible, git_gutter will be triggered
        by `on_activate()` later. So it's useless here.
        """
        if self.live_mode() and self.is_view_visible(view):
            self.debounce(view, 'modified')

    def on_clone(self, view):
        """Run git_gutter for a cloned view."""
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
        """Run git_gutter if the view gets activated.

        When opening larger files, this event is received before `on_load()`
        event and content is not yet fully available. So drop the event if
        the view is still loading or marked as scratch.
        """
        if view.is_scratch() or view.is_loading():
            return

        if self.live_mode() or self.focus_change_mode():
            self.debounce(view, 'activated')

    def on_hover(self, view, point, hover_zone):
        """Open diff popup if user hovers the mouse over the gutter area.

        Arguments:
            view        - object of the view which detected the mouse movement
            point       - provides the position where the mouse pointer is
            hover_zone  - defines the context the event was triggered in
        """
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

    def debounce(self, view, event_type):
        """Invoke evaluation of changes after some idle time.

        Arguments:
            view        - object of the view to perform evaluation for
            event_type  - a string identifying the event
        """
        key = view.id()
        this_event = time()
        self._latest_events[key] = this_event

        def callback():
            if this_event == self._latest_events.get(key, None):
                view.run_command('git_gutter')
        self.set_timeout(callback, settings.get("debounce_delay", 1000))

    def live_mode(self):
        """Evaluate changes every time the view is modified."""
        return settings.get('live_mode', True)

    def focus_change_mode(self):
        """Evaluate changes every time a view gets the focus."""
        return settings.get('focus_change_mode', True)

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
