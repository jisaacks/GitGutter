import git_gutter_handler

class ViewCollection:
  views = {}
  @staticmethod
  def add(view):
    print 'start---------------------------------------'
    f = ViewCollection.get_key(view)
    if f in ViewCollection.views:
      print 'about to reset: ' + f
      ViewCollection.views[f].reset()
    else:
      print 'about to add: ' + f
      ViewCollection.views[f] = git_gutter_handler.GitGutterHandler(view)
      ViewCollection.views[f].reset()
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
    f = ViewCollection.get_key(view)
    return ViewCollection.views[f].diff()