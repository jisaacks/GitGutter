# -*- coding: utf-8 -*-
import sublime

PLATFORM = sublime.platform()
WIN32 = PLATFORM == 'windows'

STVER = int(sublime.version())
ST3 = STVER >= 3000


def log_message(msg):
    """Print a message to statusbar and log in console."""
    msg = 'GitGutter: {0}'.format(msg)
    print(msg)
    sublime.status_message(msg)


def line_from_kwargs(view, kwargs):
    """Parse kwargs for line or point key and return line number."""
    line = kwargs.get('line')
    if line is None:
        point = kwargs.get('point')
        if point is None:
            selection = view.sel()
            if not selection:
                return
            point = selection[0].end()
        # get line number from text point
        line = view.rowcol(point)[0]
    return line
