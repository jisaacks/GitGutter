# -*- coding: utf-8 -*-
import os.path
import sublime
import sublime_plugin

from .utils import PLATFORM
from .utils import STVER
from .utils import ST3


def get(key, default=None):
    """Get a value from GitGutter.sublime-settings.

    This function provides secure access to the package settings by loading
    the settings file on demand.

    Arguments:
        key (string): The setting to read.
        default (any): The value to return if 'key' is not available.

    Returns:
        any: The value from settings file if loaded and key exists or the
            default value provided from the caller.
    """
    try:
        settings = get.settings
    except AttributeError:
        settings = sublime.load_settings('GitGutter.sublime-settings')
        get.settings = settings
    return settings.get(key, default)


class ViewSettings(object):
    """The class provides a layer to merge view and package settings.

    The ViewSettings class provides a common interface to support
    view or project based GitGutter settings. All settings found in the
    GitGutter.sublime-settings file can be placed in Preferences or the
    settings of a *.sublime-project file as well by simply prepending the
    'git_gutter_'. This even allows temporary changes for single views.

    Note:
        The only exception is 'git_binary' setting, which is NOT prefixed.
        It is searched in all settings files as 'git_binary'.

    Example:
        GitGutter.sublime-settings
        {
            show_in_minimap: 3
        }

        Preferences.sublime-settings
        {
            git_gutter_show_in_minimap: 3
        }

        Project.sublime-project
        {
            ...
            settings:
            {
                ...
                git_gutter_show_in_minimap: 3
                ...
            }
        }
    """

    # The built in themes path
    _PACKAGE_THEMES = ('%s/GitGutter/themes' % ('Packages' if ST3 else '..'))
    # A map to translate between settings and git arguments
    _IGNORE_WHITESPACE = {
        'none': '',
        'cr': '--ignore-cr-at-eol',
        'eol': '--ignore-space-at-eol',
        'space': '-b',
        'all': '-w'
    }
    # A map to translate between settings and git arguments
    _DIFF_ALGORITHM = {
        'minimal': '--minimal',
        'patience': '--patience',
        'histogram': '--histogram'
    }

    def __init__(self, view):
        """Initialize a ViewSettings object.

        Arguments:
            view (View): The view object whose settings to attach to
                the created ViewSettings object.
        """
        # view settings object
        self._settings = view.settings()
        # cached theme path to reduce calls of find_resources
        self._theme_path = ''

    def get(self, key, default=None):
        """Get a setting from attached view or GitGutter settings.

        Arguments:
            key (string): The setting to read.
            default (any): The default value to return if the setting does
                not exist in the view or GitGutter settings.

        Returns:
            any: The read value or default.
        """
        result = self._settings.get('git_gutter_' + key)
        if result is not None:
            return result
        return get(key, default)

    @property
    def show_in_minimap(self):
        """The appropiatly limited show_in_minimap setting."""
        width = self.get('show_in_minimap', 1) if ST3 else 0
        return width if width >= 0 else 100000

    @property
    def theme_path(self):
        """Read 'theme' setting and return path to gutter icons."""
        theme = self.get('theme')
        if not theme:
            theme = 'Default.gitgutter-theme'
        # rebuilt path if setting changed
        if theme != os.path.basename(self._theme_path):
            if ST3:
                themes = sublime.find_resources(theme)
                self._theme_path = (
                    os.path.dirname(themes[-1])
                    if themes else self._PACKAGE_THEMES + '/Default')
            else:
                # ST2 doesn't support find_resource, use built-in themes only.
                theme, _ = os.path.splitext(theme)
                self._theme_path = '/'.join((self._PACKAGE_THEMES, theme))
        return self._theme_path

    @property
    def git_binary(self):
        """Return the git executable path from settings or just 'git'.

        Try to get the absolute git executable path from any of the settings
        files (view/project/user/gitgutter). If none is set just return 'git'
        and let subprocess.POpen use the PATH environment variable to find the
        executable path on its own.

        Returns:
            string: Absolute path of the git executable from settings or 'git'.
        """
        value = self._settings.get('git_binary')
        if value is None:
            value = get('git_binary')
        if isinstance(value, dict):
            git_binary = value.get(PLATFORM) or value.get('default')
        else:
            git_binary = value
        return os.path.expandvars(git_binary) if git_binary else 'git'

    @property
    def ignore_whitespace(self):
        """The git ignore whitespace command line argument from settings."""
        try:
            return self._IGNORE_WHITESPACE[self.get('ignore_whitespace')]
        except KeyError:
            return None

    @property
    def diff_algorithm(self):
        """The git diff algorithm command line argument from settings.

        Returns:
            string:
                One of (--minimal, --patience, --histogram)
                or None if setting is invalid.
        """
        return self._DIFF_ALGORITHM.get(self.get('diff_algorithm'))


class GitGutterOpenFileCommand(sublime_plugin.ApplicationCommand):
    """This is a wrapper class for SublimeText's `open_file` command.

    The task is to hide the command in menu if `edit_settings` is available.
    """

    @staticmethod
    def run(file):
        """Expand variables and open the resulting file.

        Note:
            For some unknown reason the `open_file` command doesn't expand
            ${platform} when called by `run_command`, so it is expanded here.
        """
        platform_name = {
            'osx': 'OSX',
            'windows': 'Windows',
            'linux': 'Linux',
        }[PLATFORM]
        file = file.replace('${platform}', platform_name)
        sublime.run_command('open_file', {'file': file})

    @staticmethod
    def is_visible():
        """Return True to to show the command in command palette and menu."""
        return STVER < 3124


class GitGutterEditSettingsCommand(sublime_plugin.ApplicationCommand):
    """This is a wrapper class for SublimeText's `open_file` command.

    Hides the command in menu if `edit_settings` is not available.
    """

    @staticmethod
    def run(**kwargs):
        """Expand variables and open the resulting file."""
        sublime.run_command('edit_settings', kwargs)

    @staticmethod
    def is_visible():
        """Return True to to show the command in command palette and menu."""
        return STVER >= 3124
