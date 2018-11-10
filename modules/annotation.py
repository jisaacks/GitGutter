# -*- coding: utf-8 -*-
import sublime

from . import templates

_HAVE_PHANTOMS = hasattr(sublime, 'Phantom')


def erase_line_annotation(view):
    if _HAVE_PHANTOMS:
        view.erase_phantoms('git_gutter_line_annotation')


class SimpleLineAnnotationTemplate(object):
    """A simple template class with the same interface as jinja2's one."""

    TEMPLATE = '⟢ {line_author} ({line_author_age}) · {line_summary}'

    # a list of variables used by this template
    variables = frozenset(['line_author', 'line_author_age', 'line_summary'])

    @classmethod
    def render(cls, **kwargs):
        """Render line annotation using a static template.

        Arguments:
            kwargs (dict):
                The dictionary with the information about the blame, which are
                provided as variables for the message template.

        Returns:
            string: The formatted annotation message.
        """
        return cls.TEMPLATE.format(kwargs)


class GitGutterLineAnnotation(object):

    # the html template to use to render the blame phantom
    HTML_TEMPLATE = """
    <body id="gitgutter-line-annotation">
        <style>
            html, body {{
                background-color: transparent;
                color: {foreground};
                font-style: {font_style};
                margin: 0;
                padding: 0;
            }}
            body {{
                margin-left: {padding};
            }}
            a {{
                color: color({foreground} blend(var(--foreground) 90%));
                text-decoration: none;
            }}
        </style>
        {text}
    </body>
    """

    def __init__(self, view, settings):
        """Initialize GitGutterLineAnnotation object."""
        # the sublime.View the status bar is attached to
        self.view = view
        # the settings.ViewSettings object which stores GitGutter' settings
        self.settings = settings
        # initialize the jinja2 template
        self.template = None

    def is_enabled(self):
        """Check if blame phantom text is enabled.

        Note:
            Keep disabled if `draw_centered` is True because ST3176 does not
            place the phantom to the correct place then.

        Returns:
            bool: True if blame phantom text is enabled, False otherwise.
        """
        if not _HAVE_PHANTOMS or self.view.settings().get('draw_centered'):
            return False
        show_phantoms = self.settings.get('show_line_annotation', 'auto')
        if show_phantoms == 'auto':
            word_wrap = self.view.settings().get('word_wrap')
            show_phantoms = word_wrap is False or \
                word_wrap == 'auto' and self.view.match_selector(0, 'source')
        if not show_phantoms:
            self.template = None
        return show_phantoms is True

    def update(self, row, **kwargs):
        """Add a git blame phantom text to the end of the current line.

        Arguments:
            row (int):
                The text row to add the phantom text to.
            kwargs (dict):
                The dictionary with the information about the blame, which are
                provided as variables for the message template.
        """
        # blame message is useful for committed content only
        if not _HAVE_PHANTOMS or kwargs['line_summary'] == 'not committed yet':
            return

        font_style, padding = 'normal', '5rem'

        try:
            style = self.view.style_for_scope('comment.line.annotation.git_gutter')
            foreground = style['foreground']
            if style['bold']:
                if style['italic']:
                    font_style = 'bold,italic'
                else:
                    font_style = 'bold'
            elif style['italic']:
                font_style = 'italic'
        except:
            foreground = 'color(var(--foreground) blend(var(--background) 30%))'

        # the end of line
        point = self.view.line(self.view.text_point(row, 0)).end()

        # set up phantom text position
        align_to = self.settings.get('line_annotation_ruler', False)
        if align_to > 0:
            rulers = self.view.settings().get('rulers')
            if rulers:
                _, col = self.view.rowcol(point)
                # at least 5em or align to last available ruler
                padding = max(
                    1, 1 + rulers[min(align_to, len(rulers)) - 1] - col
                ) * self.view.em_width()

        # validate the template
        if not self.template:
            self.template = templates.create(
                self.settings, 'line_annotation_text', SimpleLineAnnotationTemplate)

        # update the phantom
        self.view.erase_phantoms('git_gutter_line_annotation')
        text = self.template.render(kwargs)
        if text:
            self.view.add_phantom(
                key='git_gutter_line_annotation',
                region=sublime.Region(point, point + 1),
                content=self.HTML_TEMPLATE.format(
                    foreground=foreground,
                    font_style=font_style,
                    padding=padding,
                    text=text),
                layout=sublime.LAYOUT_INLINE
            )
