# -*- coding: utf-8 -*-
import sublime


def log_message(msg):
    """Print a message to statusbar and log in console."""
    msg = 'GitGutter: {0}'.format(msg)
    print(msg)
    sublime.status_message(msg)
