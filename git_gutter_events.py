import sublime
import sublime_plugin
from view_collection import ViewCollection


class GitGutterEvents(sublime_plugin.EventListener):
    def on_load(self, view):
        ViewCollection.add(view)

    def on_modified(self, view):
        if view.settings().get('git_gutter_live_mode', True):
            # Sublime Text is very strict on the amount of time plugin
            # uses in performance-critical events. Sometimes invoking plugin
            # from this event causes Sublime warning to appear, so we need to
            # schedule its run for future.
            sublime.set_timeout(lambda: ViewCollection.add(view), 1)

    def on_clone(self, view):
        ViewCollection.add(view)

    def on_post_save(self, view):
        ViewCollection.add(view)

    def on_activated(self, view):
        ViewCollection.add(view)
