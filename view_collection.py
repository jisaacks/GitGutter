import git_gutter_handler

class ViewCollection:
  views = {}
  @staticmethod
  def add(view):
    key = ViewCollection.get_key(view)
    if not key in ViewCollection.views:
      ViewCollection.views[key] = git_gutter_handler.GitGutterHandler(view)
    ViewCollection.views[key].reset()

  @staticmethod
  def git_path(view):
    key = ViewCollection.get_key(view)
    if key in ViewCollection.views:
      return ViewCollection.views[key].get_git_path()
    else:
      return False

  @staticmethod
  def get_key(view): 
    return view.file_name()

  @staticmethod
  def diff(view):
    key = ViewCollection.get_key(view)
    return ViewCollection.views[key].diff()