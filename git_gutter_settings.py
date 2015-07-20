import sublime

ST3 = int(sublime.version()) >= 3000

def plugin_loaded():
  GitGutterSettings.load_settings()

class GitGutterSettings:
  settings = None

  @classmethod
  def get(cls, key, default):
    if (cls.settings is None or cls.settings.has(key) == False):
      cls.load_settings()

    return cls.settings.get(key, default)

  @classmethod
  def set(cls, key, value):
    if cls.settings is None:
      return None
    else:
      return cls.settings.set(key, value)

  @classmethod
  def load_settings(cls):
      cls.settings = sublime.load_settings('GitGutter.sublime-settings')
      cls.user_settings = sublime.load_settings('Preferences.sublime-settings')

      # Git Binary Setting
      cls.git_binary_path = 'git'
      git_binary = cls.user_settings.get('git_binary') or cls.settings.get('git_binary')
      if git_binary:
          cls.git_binary_path = git_binary

      # Ignore White Space Setting
      cls.ignore_whitespace = cls.settings.get('ignore_whitespace')
      if cls.ignore_whitespace == 'all':
          cls.ignore_whitespace = '-w'
      elif cls.ignore_whitespace == 'eol':
          cls.ignore_whitespace = '--ignore-space-at-eol'
      else:
          cls.ignore_whitespace = ''

      # Patience Setting
      cls.patience_switch = ''
      patience = cls.settings.get('patience')
      if patience:
          cls.patience_switch = '--patience'

      # Untracked files
      cls.show_untracked = cls.settings.get(
          'show_markers_on_untracked_file')

      # Show information in status bar
      cls.show_status = cls.user_settings.get('show_status') or cls.settings.get('show_status')
      if cls.show_status != 'all' and cls.show_status != 'none':
          cls.show_status = 'default'

  @classmethod
  def compare_against(cls):
      return cls.get('git_gutter_compare_against', 'HEAD')

if not ST3:
  plugin_loaded()