import os
import shutil
import sublime

ST3 = int(sublime.version()) >= 3000

settings = None


def plugin_loaded():
    settings.load_settings()


class GitGutterSettings:
    git_binary_path_error_shown = False
    git_binary_path_fallback = None

    def __init__(self):
        self._settings = None
        self._user_settings = None
        self._git_binary_path_fallback = None
        # These settings have public getters as they go through more
        # complex initialization than just getting the value from settings.
        self.git_binary_path = None
        self.ignore_whitespace = False
        self.patience_switch = ''
        self.show_in_minimap = False
        self.show_status = 'none'

    def get(self, key, default=None):
        if self._settings is None or not self._settings.has(key):
            self.load_settings()
        return self._settings.get(key, default)

    def set(self, key, value):
        if self._settings is None:
            self.load_settings()
        return self._settings.set(key, value)

    def load_settings(self):
        self._settings = sublime.load_settings('GitGutter.sublime-settings')
        self._user_settings = sublime.load_settings(
            'Preferences.sublime-settings')

        # Git Binary Setting
        git_binary_setting = (
            self._user_settings.get("git_binary") or
            self._settings.get("git_binary"))
        if isinstance(git_binary_setting, dict):
            self.git_binary_path = git_binary_setting.get(sublime.platform())
            if not self.git_binary_path:
                self.git_binary_path = git_binary_setting.get('default')
        else:
            self.git_binary_path = git_binary_setting

        if self.git_binary_path:
            self.git_binary_path = os.path.expandvars(self.git_binary_path)
        elif self._git_binary_path_fallback:
            self.git_binary_path = self._git_binary_path_fallback
        elif ST3:
            self.git_binary_path = shutil.which("git")
            GitGutterSettings.git_binary_path_fallback = self.git_binary_path
        else:
            git_exe = "git.exe" if sublime.platform() == "windows" else "git"
            for folder in os.environ["PATH"].split(os.pathsep):
                path = os.path.join(folder.strip('"'), git_exe)
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    self.git_binary_path = path
                    GitGutterSettings.git_binary_path_fallback = path
                    break

        if not self.git_binary_path:
            if not GitGutterSettings.git_binary_path_error_shown:
                GitGutterSettings.git_binary_path_error_shown = True
                msg = ("Your Git binary cannot be found. If it is installed, "
                       "add it to your PATH environment variable, or add "
                       "a `git_binary` setting in the "
                       "`User/GitGutter.sublime-settings` file.")
                sublime.error_message(msg)
                raise ValueError("Git binary not found.")

        # Ignore White Space Setting
        self.ignore_whitespace = self._settings.get('ignore_whitespace')
        if self.ignore_whitespace == 'all':
            self.ignore_whitespace = '-w'
        elif self.ignore_whitespace == 'eol':
            self.ignore_whitespace = '--ignore-space-at-eol'
        else:
            self.ignore_whitespace = ''

        # Patience Setting
        self.patience_switch = ''
        if self._settings.get('patience'):
            self.patience_switch = '--patience'

        # Show in minimap
        self.show_in_minimap = (
            self._user_settings.get('show_in_minimap') or
            self._settings.get('show_in_minimap'))

        # Show information in status bar
        self.show_status = (
            self._user_settings.get('show_status') or
            self._settings.get('show_status'))
        if self.show_status != 'all' and self.show_status != 'none':
            self.show_status = 'default'

settings = GitGutterSettings()

if not ST3:
    plugin_loaded()
