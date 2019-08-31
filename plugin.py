# -*- coding: utf-8 -*-
"""Load and Unload all GitGutter modules.

This module exports __all__ modules, which Sublime Text needs to know about.
The list of __all__ exported symbols is defined in modules/__init__.py.
"""


def clear_submodules():
    """Force ST to reload all submodules.

    This function deletes GitGutter's `modules` package from `sys.modules` in
    order to force ST's python to import them again.
    """
    import sys

    # not supported by ST2
    if not __package__:
        return

    prefix = __package__ + "."  # don't clear the base package
    for module_name in [
            module_name for module_name in sys.modules
            if module_name.startswith(prefix) and module_name != __name__]:
        del sys.modules[module_name]


clear_submodules()


try:
    from .modules import *
except ValueError:
    from modules import *
except ImportError:
    # Failed to import at least one module. This can happen after upgrade due
    # to internal structure changes.
    import sublime
    sublime.message_dialog(
        "GitGutter failed to reload some of its modules.\n"
        "Please restart Sublime Text!")
