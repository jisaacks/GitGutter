import sublime
import sublime_plugin
import view_collection

class GitGutterEvents(sublime_plugin.EventListener):

  def on_load(self, view):
    view_collection.ViewCollection.add(view)

  def on_modified(self, view):
    if view.settings().get('git_gutter_live_mode', True):
      view_collection.ViewCollection.add(view)

  def on_clone(self, view):
    view_collection.ViewCollection.add(view)

  def on_post_save(self, view):
    view_collection.ViewCollection.add(view)