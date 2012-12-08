import sublime, sublime_plugin

class GitGutterEvents(sublime_plugin.EventListener):
  def on_new(self, view):
    view.run_command('git_gutter')

  def on_load(self, view):
    view.run_command('git_gutter')

  def on_modified(self, view):
    view.run_command('git_gutter')

  def on_clone(self, view):
    view.run_command('git_gutter')