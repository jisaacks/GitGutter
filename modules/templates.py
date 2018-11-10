# -*- coding: utf-8 -*-
"""JINJA2 Template Cache Manager module.

The module acts as intermediate layer to make use of jinja2 library if it is
available but keep running smoothly if not.
"""
try:
    # avoid exceptions if dependency is not yet satisfied
    from jinja2 import meta
    from jinja2 import Environment
    from jinja2 import TemplateSyntaxError
    from weakref import WeakValueDictionary

    from .utils import log_message

    # jinja environment to use to create templates
    _jinja_env = Environment()
    # template cache to reuse existing templates
    _templates_cache = WeakValueDictionary()

    def create(settings, key, simple_template):
        """Create a template from source and store a weak reference as cache.

        Instead of creating a `Template` per view, the source of the template
        is used to identify the template and reuse one `Template` object for
        each matching source read from the view's settings.

        If no custom (view-, syntax-, project-specific) template is set
        up anywhere this dictionary holds only one `Template` normally.

        Arguments:
            settings (Settings):
                An settings object which can be queried via `get` to read the
                source of the template.
            key (string):
                The settings key to use to read the template source.
            simple_template (class):
                The class to instantiate, if jinja2 failed to compile the
                template source.

        Returns:
            jinja2.Template:
                if jinja2 is available and a valid template is defined
            SimpleTemplate:
                if jinnja2 is not present or failed loading the Template
        """
        # read the template from settings
        source = settings.get(key)
        if not source:
            return simple_template()
        # join a list of lines to a single source.
        if isinstance(source, list):
            source = ''.join(source)

        key = hash(source)
        try:
            # try the cached template
            return _templates_cache[key]
        except KeyError:
            try:
                # create the template from source string
                template = _jinja_env.from_string(source)
                # generate a list of all variables being in use by the template
                setattr(template, 'variables', set(
                    meta.find_undeclared_variables(_jinja_env.parse(source))))
                _templates_cache[key] = template
                return template
            except TemplateSyntaxError:
                log_message('"{}" contains malformed template!'.format(key))
        return simple_template()

except ImportError:

    def create(settings, key, simple_template):
        """Always return a simple template.

        Arguments:
            settings (Settings):
                not used
            key (string):
                not used
            simple_template (class):
                The class to instantiate

        Returns:
            SimpleTemplate:
                Always returns the instantiated simple template.
        """
        return simple_template()
