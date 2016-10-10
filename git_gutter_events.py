import time

import sublime
import sublime_plugin

ST3 = int(sublime.version()) >= 3000
if ST3:
    from .git_gutter_settings import settings
    from .view_collection import ViewCollection
    from .git_gutter_popup import show_diff_popup
else:
    from git_gutter_settings import settings
    from view_collection import ViewCollection
    from git_gutter_popup import show_diff_popup


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
        if self.live_mode():
            self.debounce(view, 'modified', ViewCollection.add)

    def on_clone(self, view):
        self.debounce(view, 'clone', ViewCollection.add)

    def on_post_save(self, view):
        self.debounce(view, 'post-save', ViewCollection.add)

    def on_load(self, view):
        if self.live_mode():
            self.debounce(view, 'load', ViewCollection.add)

    def on_activated(self, view):
        if self.focus_change_mode():
            self.debounce(view, 'activated', ViewCollection.add)

    def on_hover(self, view, point, hover_zone):
        if hover_zone != sublime.HOVER_GUTTER:
            return
        # don't let the popup flicker / fight with other packages
        if view.is_popup_visible():
            return
        if not settings.get("enable_hover_diff_popup"):
            return
        show_diff_popup(view, point, flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY)

    # Asynchronous

    def debounce(self, view, event_type, func):
        if self.non_blocking():
            key = (event_type, view.file_name())
            this_keypress = time.time()
            self.latest_keypresses[key] = this_keypress

            def callback():
                latest_keypress = self.latest_keypresses.get(key, None)
                if this_keypress == latest_keypress:
                    func(view)

            if ST3:
                set_timeout = sublime.set_timeout_async
            else:
                set_timeout = sublime.set_timeout

            set_timeout(callback, settings.get("debounce_delay"))
        else:
            func(view)

    # Settings

    def live_mode(self, default=True):
        return settings.get('live_mode', default)

    def focus_change_mode(self, default=True):
        return settings.get('focus_change_mode', default)

    def non_blocking(self, default=True):
        return settings.get('non_blocking', default)
