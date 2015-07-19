import sublime

ST3 = int(sublime.version()) >= 3000

class GitGutterSettings:
  loaded_settings = None

  @classmethod
  def get(cls, key, default):
    if (cls.loaded_settings is None or cls.loaded_settings.has(key) == False):
      cls.loaded_settings = sublime.load_settings('GitGutter.sublime-settings')

    return cls.loaded_settings.get(key, default)

  @classmethod
  def set(cls, key, value):
    if cls.loaded_settings is None:
      return None
    else:
      return cls.loaded_settings.set(key, value)