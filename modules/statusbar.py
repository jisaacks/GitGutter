# -*- coding: utf-8 -*-
import weakref

try:
    # avoid exceptions if dependency is not yet satisfied
    from jinja2 import Template
    from jinja2 import TemplateSyntaxError
    _HAVE_JINJA2 = True
except ImportError:
    _HAVE_JINJA2 = False

from .utils import log_message

# template cache to reuse existing templates
templates_cache = weakref.WeakValueDictionary()


class SimpleStatusBarTemplate(object):
    """A simple template class with the same interface as jinja2's one."""

    @staticmethod
    def render(repo=None, branch=None, compare=None, inserted=0, deleted=0,
               modified=0, **kwargs):
        """Format the status bar text using a static set of rules.

        Arguments:
            repo (string): The repository name
            branch (string): The branch name.
            compare (string): The compared branch/tag/commit
            inserted (int): The amount of inserted lines
            deleted (int): The amount of deleted lines
            modified (int): The amount of modified lines

        Returns:
            string: The formatted message to display in the status bar.
        """
        if not repo or not branch:
            return ''

        parts = ['{repo}/{branch}']

        # Compare against
        if compare not in ('HEAD', branch, None):
            parts.append('Comparing against {compare}')

        # File statistics
        if inserted:
            parts.append('{inserted}+')
        if deleted:
            parts.append('{deleted}-')
        if modified:
            parts.append(u'{modified}≠')

        # join template and fill with locals
        return ', '.join(parts).format(**locals())


class GitGutterStatusBar(object):
    """The class manages status bar text rendering.

    It stores all information, which might get displayed in the status bar
    and provides functions to partially update them.
    """

    def __init__(self, view, settings):
        """Initialize object."""
        # the sublime.View the status bar is attached to
        self.view = view
        # the settings.ViewSettings object which stores GitGutter' settings
        self.settings = settings
        # initialize the jinja2 template
        self.template = None

        # the variables to use to render the status bar
        self.vars = {
            # the repository name
            'repo': None,
            # the active branch name
            'branch': None,
            # the branch we compare against
            'compare': None,
            # the upstream branch name
            'remote': None,
            # the commits the local is ahead of upstream
            'ahead': 0,
            # the commits the local is behind of upstream
            'behind': 0,

            # repository statistics
            'added_files': 0,
            'deleted_files': 0,
            'modified_files': 0,
            'staged_files': 0,

            # file statistics
            'state': None,
            'deleted': 0,
            'inserted': 0,
            'modified': 0,
        }

    def is_enabled(self):
        """Return whether status bar text is enabled in settings or not."""
        enabled = self.settings.get('show_status_bar_text', False)
        if self.template and not enabled:
            self.template = None
            self.vars['repo'] = None
            self.erase()
        return enabled

    def erase(self):
        """Erase status bar text."""
        self.view.erase_status('00_git_gutter')

    def update(self, **kwargs):
        """Update a set of variables and redraw the status bar text.

        Arguments:
            kwargs (dict):
                The dictionary of possibly changed variables to update the
                status bar text with.
        Raises:
            KeyError, if `kwargs` contains unknown variables.
        """
        want_update = False
        for key, value in kwargs.items():
            if self.vars[key] != value:
                self.vars[key] = value
                want_update = True

        if want_update:
            if not self.template:
                self.template = self.validate_template()
            self.view.set_status(
                '00_git_gutter', self.template.render(**self.vars))

    def validate_template(self):
        """Create a template from source and store a weak reference as cache.

        Instead of creating a `Template` per view, the source of the template
        is used to identify the template and reuse one `Template` object for
        each matching source read from the view's settings.

        If no custom (view-, syntax-, project-specific) statusbar text is set
        up anywhere this dictionary holds only one `Template` normally.

        Returns:
            jinja2.Template:
                if jinja2 is available and a valid template is defined
            SimpleStatusBarTemplate:
                if jinnja2 is not present or failed loading the Template
        """
        if _HAVE_JINJA2:
            # read the template from settings
            source = self.settings.get('status_bar_text')
            if source:
                # join a list of lines to a single source.
                if isinstance(source, list):
                    source = ''.join(source)

                key = hash(source)
                try:
                    # try the cached template
                    return templates_cache[key]
                except KeyError:
                    try:
                        # create new template
                        templates_cache[key] = Template(source)
                        return templates_cache[key]
                    except TemplateSyntaxError:
                        log_message(
                            '"status_bar_text" contains malformed template!')
        return SimpleStatusBarTemplate()
