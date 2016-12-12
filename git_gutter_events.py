import time

import sublime
import sublime_plugin

try:
    from .git_gutter_settings import settings
except (ImportError, ValueError):
    from git_gutter_settings import settings

try:
    set_timeout = sublime.set_timeout_async
except AttributeError:
    set_timeout = sublime.set_timeout


class GitGutterEvents(sublime_plugin.EventListener):
    """The EventListener invokes evaluation of changes on certain events.

    GitGutter mainly operates in the background by listening to events sent
    from Sublime Text. This event listener is the interface to get informed
    about user interaction to decide when to invoke an evaluation of changes
    by calling the main `git_gutter` command.
    """

    def __init__(self):
        """Initialize GitGutterEvents object."""
        self._latest_events = {}

    def on_load(self, view):
        """Run git_gutter after loading, if view is valid.

        Arguments:
            view (View): The view which received the event.
        """
        self.debounce(view, 'load')

    def on_close(self, view):
        """Clean up the debounce dictinary.

        Arguments:
            view (View): The view which received the event.
        """
        key = view.id()
        if key in self._latest_events:
            del self._latest_events[key]

    def on_modified(self, view):
        """Run git_gutter for modified visible view.

        The `on_modified()` is called when typing into an active view and
        might be called for inactive views if the file changes on disk.

        Arguments:
            view (View): The view which received the event.
        """
        if self.live_mode():
            self.debounce(view, 'modified')

    def on_clone(self, view):
        """Run git_gutter for a cloned view.

        Arguments:
            view (View): The view which received the event.
        """
        self.debounce(view, 'clone')

    def on_post_save(self, view):
        """Run git_gutter after saving.

        Arguments:
            view (View): The view which received the event.
        """
        self.debounce(view, 'post-save')

    def on_activated(self, view):
        """Run git_gutter if the view gets activated.

        When opening larger files, this event is received before `on_load()`
        event and content is not yet fully available. So drop the event if
        the view is still loading or marked as scratch.

        Arguments:
            view (View): The view which received the event.
        """
        if self.live_mode() or self.focus_change_mode():
            self.debounce(view, 'activated')

    @staticmethod
    def on_hover(view, point, hover_zone):
        """Open diff popup if user hovers the mouse over the gutter area.

        Arguments:
            view (View): The view which received the event.
            point (Point): The text position where the mouse hovered
            hover_zone (int): The context the event was triggered in
        """
        if hover_zone != sublime.HOVER_GUTTER:
            return
        # don't let the popup flicker / fight with other packages
        if view.is_popup_visible():
            return
        if not settings.get('enable_hover_diff_popup'):
            return
        view.run_command('git_gutter_diff_popup', {
            'point': point, 'flags': sublime.HIDE_ON_MOUSE_MOVE_AWAY})

    def debounce(self, view, event_type):
        """Invoke evaluation of changes after some idle time.

        Arguments:
            view (View): The view to perform evaluation for
            event_type (string): The event identifier
        """
        key = view.id()
        this_event = time.time()
        self._latest_events.setdefault(key, {})[event_type] = this_event

        def callback():
            """Run git_gutter command for most recent event."""
            if not self.is_view_visible(view):
                return
            view_events = self._latest_events.get(key, {})
            if this_event == view_events.get(event_type, None):
                view.run_command('git_gutter', {
                    'event_type': list(view_events.keys())})
                self._latest_events[key] = {}
        # Run command delayed and asynchronous if supported.
        set_timeout(callback, max(300, settings.get('debounce_delay', 1000)))

    @staticmethod
    def live_mode():
        """Evaluate changes every time the view is modified."""
        return settings.get('live_mode', True)

    @staticmethod
    def focus_change_mode():
        """Evaluate changes every time a view gets the focus."""
        return settings.get('focus_change_mode', True)

    @staticmethod
    def is_view_visible(view):
        """Determine if the view is visible.

        Only an active view of a group is visible.

        Returns:
            bool: True if the view is visible in any window.
        """
        window = view.window()
        if window:
            view_id = view.id()
            for group in range(window.num_groups()):
                active_view = window.active_view_in_group(group)
                if active_view and active_view.id() == view_id:
                    return True
        return False
