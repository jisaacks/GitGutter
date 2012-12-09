import git_helper, sublime, sys

class GitGutterHandler:
  def __init__(self, view):
    self.view = view
    self.git_path = git_helper.git_file_path(self.view)
    self.reset()

  def reset(self):
    if self.git_path:
      self.view.run_command('git_gutter')

  def get_git_path(self):
    return self.git_path

  def diff(self):
    # chars = self.view.size()
    # region = sublime.Region(0,chars)
    # contents = self.view.substr(region)
    # print contents

    if self.git_path:
      contents = sys.run_and_return('git','show','head:'+self.git_path)
      return contents
    else:
      return False