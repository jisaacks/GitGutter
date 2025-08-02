"""Support Information module.

The module provides functions to gain information to be included in issues.
It neither contains normal functionality nor is it used by GitGutter.
"""
import os
import subprocess
import textwrap

import sublime
import sublime_plugin

# get absolute path of the package
try:
    PACKAGE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__spec__.origin)))
except (AttributeError, NameError):
    PACKAGE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.isfile(PACKAGE_PATH):
    # Package is a PACKAGE.sublime-package so get its filename
    PACKAGE, _ = os.path.splitext(os.path.basename(PACKAGE_PATH))
elif os.path.isdir(PACKAGE_PATH):
    # Package is a directory, so get its basename
    PACKAGE = os.path.basename(PACKAGE_PATH)
else:
    raise ValueError('Package is no file and no directory!')


def git(*args):
    """Read version of git binary."""
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    else:
        startupinfo = None
    proc = subprocess.Popen(
        args=['git'] + [arg for arg in args], startupinfo=startupinfo,
        stdout=subprocess.PIPE, stdin=subprocess.PIPE,
        # run command in package directory if exists.
        cwd=PACKAGE_PATH if os.path.isdir(PACKAGE_PATH) else None)
    stdout, _ = proc.communicate()
    return stdout.decode('utf-8').strip() if stdout else None


def git_version():
    """Read version of git binary."""
    try:
        return git('--version')
    except Exception as exception:
        print('%s: %s' % (PACKAGE, exception))
        return 'git version could not be acquired!'


def gitgutter_version():
    """Read commit hash or version of GitGutter."""
    try:
        return git('rev-parse', 'HEAD')[:7]
    except:
        try:
            return sublime.load_resource(
                'Packages/%s/VERSION' % PACKAGE).strip()
        except Exception as exception:
            print('%s: %s' % (PACKAGE, exception))
            return 'Version could not be acquired!'


def module_version(module, attr):
    """Format the module version."""
    try:
        version = getattr(module, attr)
        if callable(version):
            version = version()
    except Exception as exception:
        print('%s: %s' % (PACKAGE, exception))
        version = 'version could not be acquired!'

    if not isinstance(version, str):
        version = '.'.join((str(x) for x in version))
    return version


def is_installed_by_package_control():
    """Check if installed by package control."""
    settings = sublime.load_settings('Package Control.sublime-settings')
    return str(PACKAGE in set(settings.get('installed_packages', [])))


class GitGutterSupportInfoCommand(sublime_plugin.ApplicationCommand):
    """Support Information Command."""

    @staticmethod
    def run():
        """Run command."""
        info = {
            'platform': sublime.platform(),
            'st_version': sublime.version(),
            'arch': sublime.arch(),
            'package_version': gitgutter_version(),
            'pc_install': is_installed_by_package_control(),
            'git_version': git_version()
        }

        try:
            import mdpopups
            info['mdpopups'] = module_version(mdpopups, 'version')
        except ImportError:
            info['mdpopups'] = 'not installed!'

        try:
            from mdpopups import jinja2
            info['jinja'] = module_version(jinja2, '__version__')
        except ImportError:
            info['jinja'] = 'not installed!'

        msg = textwrap.dedent(
            """\
            - Sublime Text %(st_version)s
            - Platform: %(platform)s
            - Arch: %(arch)s
            - GitGutter %(package_version)s
            - Install via PC: %(pc_install)s
            - %(git_version)s
            - mdpopups %(mdpopups)s
            - jinja2 %(jinja)s
            """ % info
        )

        sublime.message_dialog(msg + '\nInfo has been copied to clipboard.')
        sublime.set_clipboard(msg)
