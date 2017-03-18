# -*- coding: utf-8 -*-
"""Load and Unload all GitGutter modules.

This module exports __all__ modules, which Sublime Text needs to know about.
The list of __all__ exported symbols is defined in modules/__init__.py.
"""

try:
    from .modules import *
except ValueError:
    from modules import *


def plugin_loaded():
    """Plugin loaded callback."""
    try:
        # Reload 'modules' once after upgrading to ensure GitGutter is ready
        # for use instantly again. (Works with ST3 and python3 only!)
        from package_control import events
        if events.post_upgrade(__package__):
            from .modules.reload import reload_package
            reload_package(__package__)
    except ImportError:
        # Fail silently if package control isn't installed.
        pass
