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

    # Synchronous

    def on_modified(self, view):
        if self.settings_loaded():
            if not self.non_blocking and self.live_mode:
                ViewCollection.add(view)

    def on_clone(self, view):
        if self.settings_loaded():
            if not self.non_blocking:
                ViewCollection.add(view)

    def on_post_save(self, view):
        if self.settings_loaded():
            if not self.non_blocking:
                ViewCollection.add(view)

    def on_load(self, view):
        if self.settings_loaded():
            if not self.non_blocking and not self.live_mode:
                ViewCollection.add(view)

    def on_activated(self, view):
        if self.settings_loaded():
            if not self.non_blocking and self.focus_change_mode:
                ViewCollection.add(view)

    # Asynchronous

    def on_modified_async(self, view):
        if self.settings_loaded():
            if self.non_blocking and self.live_mode:
                ViewCollection.add(view)

    def on_clone_async(self, view):
        if self.settings_loaded():
            if self.non_blocking:
                ViewCollection.add(view)

    def on_post_save_async(self, view):
        if self.settings_loaded():
            if self.non_blocking:
                ViewCollection.add(view)

    def on_load_async(self, view):
        if self.settings_loaded():
            if self.non_blocking and not self.live_mode:
                ViewCollection.add(view)

    def on_activated_async(self, view):
        if self.settings_loaded():
            if self.non_blocking and self.focus_change_mode:
                ViewCollection.add(view)

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
        if self.non_blocking is None or int(sublime.version()) < 3014:
            self.non_blocking = False

        return True

def plugin_loaded():
    global settings
    settings = sublime.load_settings('GitGutter.sublime-settings')

if not ST3:
    plugin_loaded()

