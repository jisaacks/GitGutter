import git_gutter_handler

class ViewCollection:
  views = {}
  @staticmethod
  def add(view):
    f = view.file_name()
    if f in ViewCollection.views:
      ViewCollection.views[f].reset()
      print 'reset: ' + f
    else:
      ViewCollection.views[f] = git_gutter_handler.GitGutterHandler(view)
      print 'added: ' + f
    for k in ViewCollection.views:
      print 'file: '+k