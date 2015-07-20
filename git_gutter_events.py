import time

import sublime
import sublime_plugin
from threading import Timer

ST3 = int(sublime.version()) >= 3000

settings = None

def plugin_loaded():
    global settings
    settings = sublime.load_settings('GitGutter.sublime-settings')

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
        self.timer = None

    def refresh(self, view, event_type):
        try:
            self.timer.cancel()
        except(AttributeError):
            pass

        self.timer = Timer(self.debounce_delay_secs(view), view.run_command, ["git_gutter"])
        self.timer.start()

    # Synchronous
    def on_modified(self, view):
        if self.live_mode(view):
            self.refresh(view, 'modified')

    def on_clone(self, view):
        self.refresh(view, 'clone')

    def on_post_save(self, view):
        self.refresh(view, 'post-save')

    def on_load(self, view):
        if self.live_mode(view):
            self.refresh(view, 'load')

    def on_activated(self, view):
        if self.focus_change_mode(view):
            self.refresh(view, 'activated')

    # Settings

    def debounce_delay_secs(self, view, default = 1000):
        return settings.get('debounce_delay', default) / 1000.0

    def live_mode(self, view, default = True):
        return settings.get('live_mode', default)

    def focus_change_mode(self, view, default = True):
        return settings.get('focus_change_mode', default)

    def non_blocking(self, view, default = True):
        return settings.get.get('non_blocking', default)

if not ST3:
    plugin_loaded()