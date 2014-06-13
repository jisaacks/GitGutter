import time

import sublime
import sublime_plugin

ST3 = int(sublime.version()) >= 3000
if ST3:
    from GitGutter.view_collection import ViewCollection
else:
    from view_collection import ViewCollection


class GitGutterEvents(sublime_plugin.EventListener):

    def __init__(self):
        self._settings_loaded = False
        self.latest_keypresses = {}

    # Synchronous

    def on_modified(self, view):
        if self.settings_loaded() and self.live_mode:
            self.debounce(view, 'modified', ViewCollection.add)

    def on_clone(self, view):
        if self.settings_loaded():
            self.debounce(view, 'clone', ViewCollection.add)

    def on_post_save(self, view):
        if self.settings_loaded():
            self.debounce(view, 'post-save', ViewCollection.add)

    def on_load(self, view):
        if self.settings_loaded() and self.live_mode:
            self.debounce(view, 'load', ViewCollection.add)

    def on_activated(self, view):
        if self.settings_loaded() and self.focus_change_mode:
            self.debounce(view, 'activated', ViewCollection.add)

    # Asynchronous

    def debounce(self, view, event_type, func):
        if self.non_blocking:
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

    on_modified_async = on_modified
    on_clone_async = on_clone
    on_post_save_async = on_post_save
    on_load_async = on_load
    on_activated_async = on_activated

    # Settings

    def settings_loaded(self):
        if settings and not self._settings_loaded:
            self._settings_loaded = self.load_settings()

        return self._settings_loaded

    def load_settings(self):
        self.live_mode = settings.get('live_mode')
        if self.live_mode is None:
            self.live_mode = True

        self.focus_change_mode = settings.get('focus_change_mode')
        if self.focus_change_mode is None:
            self.focus_change_mode = True

        self.non_blocking = settings.get('non_blocking')
        if self.non_blocking is None:
            self.non_blocking = True

        return True

settings = {}


def plugin_loaded():
    global settings
    settings = sublime.load_settings('GitGutter.sublime-settings')

if not ST3:
    plugin_loaded()
