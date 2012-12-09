import git_gutter_handler

class ViewCollection:
  views = {}
  @staticmethod
  def add(view):
    f = ViewCollection.get_key(view)
    if f in ViewCollection.views:
      ViewCollection.views[f].reset()
      print 'reset: ' + f
    else:
      ViewCollection.views[f] = git_gutter_handler.GitGutterHandler(view)
      print 'added: ' + f
    for k in ViewCollection.views:
      print 'file: '+k

  @staticmethod
  def git_path(view):
    f = ViewCollection.get_key(view)
    if f in ViewCollection.views:
      return ViewCollection.views[f].get_git_path()
    else:
      return False

  @staticmethod
  def get_key(view):
    return view.file_name()

  @staticmethod
  def diff(view):
    if ViewCollection.git_path(view):
      f = ViewCollection.get_key(view)
      return ViewCollection.views[f].diff()
    else:
      return False