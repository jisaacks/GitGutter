import sublime
import sublime_plugin
try:
    from GitGutter.view_collection import ViewCollection
except ImportError:
    from view_collection import ViewCollection

class GitGutterEvents(sublime_plugin.EventListener):
    def __init__(self):
        self.load_settings()

    def on_modified(self, view):
        if self.live_mode:
            ViewCollection.add(view)

    def on_clone(self, view):
        ViewCollection.add(view)

    def on_post_save(self, view):
        ViewCollection.add(view)

    def on_activated(self, view):
        ViewCollection.add(view)

    def load_settings(self):
        self.settings = sublime.load_settings('GitGutter.sublime-settings')
        self.live_mode = self.settings.get('live_mode')