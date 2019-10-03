"""Diff Popup Module initialization.

Check dependencies and enable/disable diff popup.
Declare public API functions.
"""
try:
    # mdpopups 2.0.0+ is required
    import mdpopups
    if mdpopups.version() < (2, 0, 0):
        raise ImportError('mdpopups 2.0.0+ required.')

    # public function
    from .factory import show_diff_popup
except ImportError:
    show_diff_popup = None
