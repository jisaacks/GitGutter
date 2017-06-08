# -*- coding: utf-8 -*-
"""Diff Popup Module initialization.

Check dependencies and enable/disable diff popup.
Declare public API functions.
"""
try:
    # mdpopups needs 3119+ for wrapper_class, which diff popup relies on
    import sublime
    if int(sublime.version()) < 3119:
        raise ImportError('Sublime Text 3119+ required.')

    # mdpopups 1.9.0+ is required because of wrapper_class and templates
    import mdpopups
    if mdpopups.version() < (1, 9, 0):
        raise ImportError('mdpopups 1.9.0+ required.')

    # mdpopups 2.0.0+ requires Sublime Text 3124+
    if mdpopups.version() >= (2, 0, 0) and int(sublime.version()) < 3124:
        raise ImportError('Sublime Text 3124+ required.')

    # public Sublime Text Commands
    from .commands import (
        GitGutterDiffPopupCommand, GitGutterReplaceTextCommand)
    # public function
    from .factory import show_diff_popup
except ImportError:
    # Some dummy interface objects to avoid import errors
    GitGutterDiffPopupCommand = None
    GitGutterReplaceTextCommand = None
    show_diff_popup = None
