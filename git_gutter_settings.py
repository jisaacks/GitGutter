import sublime

class GitGutterSettings:

  def __init__(self):
    self.settings = None
    # a mapping of git_dir to a string indicating what to compare against.
    # ex:
    #   /Users/foo/workspace1/.git -> "origin",
    #   /Users/foo/workspace2/.git -> "HEAD"
    self.compare_against_mapping = {}

  def get(self, key, default):
    if (self.settings is None or self.settings.has(key) == False):
      self.load_settings('get')
    return self.settings.get(key, default)

  def set(self, key, value):
    if self.settings is None:
      self.load_settings('set')
    return self.settings.set(key, value)

  def load_settings(self, msg):
      self.settings = sublime.load_settings('GitGutter.sublime-settings')
      self.user_settings = sublime.load_settings('Preferences.sublime-settings')

      # Git Binary Setting
      self.git_binary_path = 'git'
      git_binary = self.user_settings.get('git_binary') or self.settings.get('git_binary')
      if git_binary:
          self.git_binary_path = git_binary

      # Ignore White Space Setting
      self.ignore_whitespace = self.settings.get('ignore_whitespace')
      if self.ignore_whitespace == 'all':
          self.ignore_whitespace = '-w'
      elif self.ignore_whitespace == 'eol':
          self.ignore_whitespace = '--ignore-space-at-eol'
      else:
          self.ignore_whitespace = ''

      # Patience Setting
      self.patience_switch = ''
      patience = self.settings.get('patience')
      if patience:
          self.patience_switch = '--patience'

      # Untracked files
      self.show_untracked = self.settings.get(
          'show_markers_on_untracked_file')

      # Show information in status bar
      self.show_status = self.user_settings.get('show_status') or self.settings.get('show_status')
      if self.show_status != 'all' and self.show_status != 'none':
          self.show_status = 'default'

  def compare_against(self, git_dir):
    if git_dir in self.compare_against_mapping:
      return self.compare_against_mapping[git_dir]
    else:
      return self.get('git_gutter_compare_against', 'HEAD')

  def set_compare_against(self, git_dir, new_compare_against):
    self.compare_against_mapping[git_dir] = new_compare_against