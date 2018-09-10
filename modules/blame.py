# -*- coding: utf-8 -*-
import time
from functools import partial

from .utils import line_from_kwargs

# A set of all supported variables
BLAME_VARIABLES = frozenset([
    'line_commit',
    'line_previous',
    'line_summary',
    'line_author',
    'line_author_mail',
    'line_author_age',
    'line_author_time',
    'line_author_tz',
    'line_committer',
    'line_committer_mail',
    'line_committer_age',
    'line_committer_time',
    'line_committer_tz'
])


def run_blame(git_gutter, **kwargs):
    """Call git blame for the requested or active row and add phantom.

    Arguments:
        git_gutter (GitGutterCommand):
            The main command object, which represents GitGutter.
        kwargs (dict):
            The arguments received from the `run_command`.
            This argument is declared to create a common interface being used
            by the GitGutterCommand object.

    Valid kwargs are:
        line (int):
            The zero based line number to run the git blame command for.
        point (int):
            The text point to use in order to calculate the line to run the
            git blame command for.
    """
    # check if feature is enabled
    show_inline = git_gutter.line_annotation.is_enabled()
    status_bar = git_gutter.status_bar
    show_status = (status_bar.is_enabled() and status_bar.has(BLAME_VARIABLES))
    if not show_inline and not show_status:
        return None

    # ignore empty lines as cursor jumps off
    view = git_gutter.view
    line = line_from_kwargs(view, kwargs)
    if not view.line(view.text_point(line, 0)):
        return None

    # run git blame and print its output to the desired targets
    return git_gutter.git_handler.git_blame(line).then(
        partial(_render_blame, git_gutter, show_inline, show_status))


def _render_blame(git_gutter, show_inline, show_status, contents):
    """Decode the git blame output and update status bar and phantoms."""
    if not contents:
        return
    contents = contents.split('\n')
    # decode first line <commit> <row committed> <row modified> <num>
    tokens = contents[0].split(' ')
    # use if second row entry if exists, the first one otherwise
    row = int(tokens[2] if len(tokens) > 2 else tokens[1]) - 1

    blame = {'line_commit': tokens[0]}
    # decode the contents excluding the first line, which contains
    # the current commit hash and blamed row, only.
    for content in contents[1:]:
        if ' ' in content:
            key, value = content.split(' ', 1)
            key = 'line_' + key.replace('-', '_').strip()
            if key in git_gutter.status_bar.vars:
                blame[key] = value

    # modify some fields if line contains uncommitted content
    if not tokens[0] != '0' * len(tokens[0]):
        blame['line_author'] = 'You'
        blame['line_committer'] = 'Nobody'
        blame['line_summary'] = 'not committed yet'

    # prepare some extra information
    author_time = int(blame['line_author_time'])
    blame['line_author_age'] = format_ago(author_time)
    blame['line_author_time'] = format_time(author_time)
    committer_time = int(blame['line_committer_time'])
    blame['line_committer_age'] = format_ago(committer_time)
    blame['line_committer_time'] = format_time(committer_time)

    # print the statusbar text if enabled
    if show_status:
        git_gutter.status_bar.update(**blame)

    # print the inline text if enabled
    if show_inline:
        git_gutter.line_annotation.update(row, **blame)


def format_ago(timestamp):
    """Return the human readable time elapsed since `timestamp`."""
    st = time.gmtime(time.time() - timestamp)
    if st.tm_year - 1970 > 1:
        return '{0} years ago'.format(st.tm_year - 1970)
    if st.tm_year - 1970 == 1:
        return 'a year ago'
    if st.tm_mon - 1 > 1:
        return '{0} months ago'.format(st.tm_mon - 1)
    if st.tm_mon - 1 == 1:
        return 'a month ago'
    if st.tm_mday - 1 > 1:
        return '{0} days ago'.format(st.tm_mday - 1)
    if st.tm_mday - 1 == 1:
        return 'a day ago'
    if st.tm_hour > 1:
        return '{0} hours ago'.format(st.tm_hour)
    if st.tm_hour == 1:
        return 'an hour ago'
    if st.tm_min > 1:
        return '{0} minutes ago'.format(st.tm_min)
    if st.tm_min == 1:
        return 'a minute ago'
    return 'just now'


def format_time(timestamp):
    """Return the human readable time of `timestamp`."""
    return time.strftime("%b %d %Y %H:%M", time.localtime(timestamp))
