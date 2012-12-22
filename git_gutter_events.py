import sublime
import sublime_plugin
from view_collection import ViewCollection


class GitGutterEvents(sublime_plugin.EventListener):
    def on_modified(self, view):
        if view.settings().get('git_gutter_live_mode', True):
            ViewCollection.add(view)

    def on_clone(self, view):
        ViewCollection.add(view)

    def on_post_save(self, view):
        ViewCollection.add(view)

    def on_activated(self, view):
        ViewCollection.add(view)
