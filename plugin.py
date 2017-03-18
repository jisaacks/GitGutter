# -*- coding: utf-8 -*-
"""Load and Unload all GitGutter modules.

This module exports __all__ modules, which Sublime Text needs to know about.
The list of __all__ exported symbols is defined in modules/__init__.py.
"""

try:
    from .modules import *
except ValueError:
    from modules import *
