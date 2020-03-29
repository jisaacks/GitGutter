# -*- coding: utf-8 -*-
"""Load and Unload all GitGutter modules.

This module exports __all__ modules, which Sublime Text needs to know about.
The list of __all__ exported symbols is defined in modules/__init__.py.
"""
import sublime

if int(sublime.version()) < 3176:
    print('GitGutter requires ST3 3176+')
else:
    import sys

    prefix = __package__ + '.'  # don't clear the base package
    for module_name in [
            module_name for module_name in sys.modules
            if module_name.startswith(prefix) and module_name != __name__]:
        del sys.modules[module_name]
    prefix = None

    from .modules import *
