class GitGutterHandler:
  def __init__(self, view):
    self.view = view
    self.reset()

  def reset(self):
    self.view.run_command('git_gutter')