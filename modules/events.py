# -*- coding: utf-8 -*-
import time

import sublime
import sublime_plugin

from . import settings
from .annotation import erase_line_annotation

# binary representation of all ST events
NEW = 1
CLONE = 2
LOAD = 4
PRE_SAVE = 8
POST_SAVE = 16
MODIFIED = 32
SELECTION_MODIFIED = 64
ACTIVATED = 128
DEACTIVATED = 256

try:
    set_timeout = sublime.set_timeout_async
except AttributeError:
    set_timeout = sublime.set_timeout


class EventListener(sublime_plugin.EventListener):
    """The EventListener invokes evaluation of changes on certain events.

    GitGutter mainly operates in the background by listening to events sent
    from Sublime Text. This event listener is the interface to get informed
    about user interaction to decide when to invoke an evaluation of changes
    by calling the main `git_gutter` command.
    """

    def __init__(self):
        """Initialize GitGutterEvents object."""
        self.view_events = {}

    def on_load(self, view):
        """Run git_gutter after loading, if view is valid.

        Arguments:
            view (View): The view which received the event.
        """
        self.debounce(view, LOAD)

    def on_close(self, view):
        """Clean up the debounce dictionary.

        Arguments:
            view (View): The view which received the event.
        """
        try:
            del self.view_events[view.id()]
        except KeyError:
            pass

    def on_modified(self, view):
        """Run git_gutter for modified visible view.

        The `on_modified()` is called when typing into an active view and
        might be called for inactive views if the file changes on disk.

        Arguments:
            view (View): The view which received the event.
        """
        self.debounce(view, MODIFIED)

    def on_clone(self, view):
        """Run git_gutter for a cloned view.

        Arguments:
            view (View): The view which received the event.
        """
        self.debounce(view, CLONE)

    def on_post_save(self, view):
        """Run git_gutter after saving.

        Arguments:
            view (View): The view which received the event.
        """
        self.debounce(view, POST_SAVE)

    def on_activated(self, view):
        """Run git_gutter if the view gets activated.

        Arguments:
            view (View): The view which received the event.
        """
        self.debounce(view, ACTIVATED)

    def on_hover(self, view, point, hover_zone):
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
        try:
            view_settings = self.view_events[view.id()].settings
        except KeyError:
            return
        # check if hover is enabled
        if not view_settings.get('enable_hover_diff_popup'):
            return
        # check protected regions
        keys = tuple(view_settings.get('diff_popup_protected_regions'))
        points = (view.line(reg).a for key in keys for reg in view.get_regions(key))
        if point in points:
            return
        # finally show the popup
        view.run_command('git_gutter_diff_popup', {
            'point': point, 'flags': sublime.HIDE_ON_MOUSE_MOVE_AWAY})

    def debounce(self, view, event_id):
        """Invoke evaluation of changes after some idle time.

        Arguments:
            view (View): The view to perform evaluation for
            event_id (int): The event identifier
        """
        key = view.id()
        try:
            self.view_events[key].push(event_id)
        except KeyError:
            if view.buffer_id():
                new_listener = ViewEventListener(view)
                new_listener.push(event_id)
                self.view_events[key] = new_listener
            # do garbage connection
            for vid in [vid for vid, listener in self.view_events.items()
                        if listener.view.buffer_id() == 0]:
                del self.view_events[vid]


class ViewEventListener(object):
    """The class queues and forwards view events to GitGutterCommand.

    A ViewEventListener object queues all events received from a view and
    starts a single sublime timer to forward the event to GitGutterCommand
    after some idle time. This ensures not to bloat sublime API due to dozens
    of timers running for debouncing events.
    """

    def __init__(self, view):
        """Initialize ViewEventListener object.

        Arguments:
            view (View): The view the object is created for.
        """
        self.view = view
        # view aware git gutter settings
        self.settings = settings.ViewSettings(view)
        # timer is running flag
        self.busy = False
        # a binary combination of above events
        self.events = 0
        # latest time of append() call
        self.latest_time = 0.0
        # debounce delay in milliseconds
        self.delay = 0

    def push(self, event_id):
        """Push the event to the queue and start idle timer.

        Add the event identifier to 'events' and update the 'latest_time'.
        This marks an event to be received rather than counting the number
        of received events. The idle timer is started only, if no other one
        is already in flight.

        Arguments:
            event_id (int): One of the event identifiers.
        """
        if event_id & ACTIVATED:
            if not (self.settings.get('live_mode') or
                    self.settings.get('focus_change_mode')):
                return
        elif event_id & MODIFIED:
            if not self.settings.get('live_mode'):
                return
        self.latest_time = time.time()
        self.events |= event_id
        if not self.busy:
            self.delay = max(200, self.settings.get('debounce_delay', 1000))
            self.start_timer(200)

    def start_timer(self, delay):
        """Run GitGutterCommand after some idle time.

        Check if no more events were received during idle time and run
        GitGutterCommand if not. Restart timer to check later, otherwise.

        Timer is stopped without calling GitGutterCommand, if a view is not
        visible to save some resources. Evaluation will be triggered by
        activating the view next time.

        Arguments:
            delay (int): The delay in milliseconds to wait until probably
                forward the events, if no other event was received in the
                meanwhile.
        """
        start_time = self.latest_time

        def worker():
            """The function called after some idle time."""
            if start_time < self.latest_time:
                self.start_timer(self.delay)
                return
            self.busy = False
            if not self.is_view_visible():
                return
            self.view.run_command('git_gutter', {'events': self.events})
            self.events = 0

        self.busy = True
        set_timeout(worker, delay)

    def is_view_visible(self):
        """Determine if the view is visible.

        Only an active view of a group is visible.

        Returns:
            bool: True if the view is visible in any window.
        """
        window = self.view.window()
        if window:
            view_id = self.view.id()
            for group in range(window.num_groups()):
                active_view = window.active_view_in_group(group)
                if active_view and active_view.id() == view_id:
                    return True
        return False


class BlameEventListener(sublime_plugin.EventListener):
    """An EventListener to track caret movement and update blame messages."""

    def __init__(self):
        """Initialize n BlameEventListener object."""
        # last blame call
        self.latest_blame_time = 0.0
        # a dictionary with active rows of each view
        self.last_blame_row = {}

    def on_close(self, view):
        """Clean up the debounce dictionary.

        Arguments:
            view (View): The view which received the event.
        """
        key = view.id()
        if key in self.last_blame_row:
            del self.last_blame_row[key]

    def on_activated(self, view):
        """Run blame if the view is activated."""
        self._run_blame(view, True)

    def on_deactivated(self, view):
        """Remove inline blame text if view is deactivated."""
        erase_line_annotation(view)

    def on_modified(self, view):
        """Remove inline blame text if user starts typing."""
        erase_line_annotation(view)

    def on_selection_modified(self, view):
        """Run blame if the caret moves to another row."""
        self._run_blame(view, False)

    def _run_blame(self, view, force):
        """Run blame if the caret moves to another row."""

        # remove existing phantoms
        erase_line_annotation(view)

        # initiate debounce timer
        blame_time = time.time()
        self.latest_blame_time = blame_time

        def on_time():
            if self.latest_blame_time != blame_time:
                return
            try:
                sel = view.sel()
                # do nothing if not exactly one cursor is visible
                if len(sel) != 1:
                    return
                sel = sel[0]
                # do nothing is selection not empty or line is empty
                if not sel.empty() or not view.line(sel.b):
                    return
                row, _ = view.rowcol(sel.b)
                # do nothing if row didn't change
                if not force and row == self.last_blame_row.get(view.id(), -1):
                    return
                self.last_blame_row[view.id()] = row
            except (AttributeError, IndexError, TypeError):
                pass
            else:
                view.run_command('git_gutter_blame')

        # don't call blame if selected row changes too quickly
        sublime.set_timeout(on_time, 400)
