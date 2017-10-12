# -*- coding: utf-8 -*-
"""Diff Popup Module initialization.

Check dependencies and enable/disable diff popup.
Declare public API functions.
"""
try:
    # mdpopups 2.0.0+ is required
    import mdpopups
    if mdpopups.version() < (2, 0, 0):
        raise ImportError('mdpopups 2.0.0+ required.')

    # mdpopups 2.0.0+ requires Sublime Text 3124+
    import sublime
    if int(sublime.version()) < 3124:
        raise ImportError('Sublime Text 3124+ required.')

    # public function
    from .factory import show_diff_popup
except ImportError:
    show_diff_popup = None
