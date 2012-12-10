import sublime
import sublime_plugin
import view_collection

class GitGutterEvents(sublime_plugin.EventListener):
  def on_new(self, view):
    view_collection.ViewCollection.add(view)

  def on_load(self, view):
    view_collection.ViewCollection.add(view)

  def on_modified(self, view):
    view_collection.ViewCollection.add(view)

  def on_clone(self, view):
    view_collection.ViewCollection.add(view)