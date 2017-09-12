"""
Validate JSON format.

Licensed under MIT
Copyright (c) 2012-2015 Isaac Muse <isaacmuse@gmail.com>

Some smaller fixes are applied by <deathaxe@gmail.com>
"""
import codecs
import fnmatch
import json
import os
import re
import unittest

RE_LINE_PRESERVE = re.compile(r"\r?\n", re.MULTILINE)
RE_COMMENT = re.compile(
    r'''(?x)
        (?P<comments>
            /\*[^*]*\*+(?:[^/*][^*]*\*+)*/  # multi-line comments
          | [ \t]*//(?:[^\r\n])*            # single line comments
        )
      | (?P<code>
            "(?:\\.|[^"\\])*"               # double quotes
          | '(?:\\.|[^'\\])*'               # single quotes
          | .[^/"']*                        # everything else
        )
    ''',
    re.DOTALL
)
RE_TRAILING_COMMA = re.compile(
    r'''(?x)
        (
            (?P<square_comma>
                ,                        # trailing comma
                (?P<square_ws>[\s\r\n]*) # white space
                (?P<square_bracket>\])   # bracket
            )
          | (?P<curly_comma>
                ,                        # trailing comma
                (?P<curly_ws>[\s\r\n]*)  # white space
                (?P<curly_bracket>\})    # bracket
            )
        )
      | (?P<code>
            "(?:\\.|[^"\\])*"            # double quoted string
          | '(?:\\.|[^'\\])*'            # single quoted string
          | .[^,"']*                     # everything else
        )
    ''',
    re.DOTALL
)
RE_LINE_INDENT_TAB = re.compile(r'^((\t+)?[^ \t\r\n][^\r\n]*)?\r?\n$')
RE_LINE_INDENT_SPACE = re.compile(r'^(((?: {4})+)?[^ \t\r\n][^\r\n]*)?\r?\n$')
RE_TRAILING_SPACES = re.compile(r'^.*?[ \t]+\r?\n?$')


E_MALFORMED = "E0"
E_COMMENTS = "E1"
E_COMMA = "E2"
W_NL_START = "W1"
W_NL_END = "W2"
W_INDENT = "W3"
W_TRAILING_SPACE = "W4"


VIOLATION_MSG = {
    E_MALFORMED: 'JSON content is malformed.',
    E_COMMENTS: 'Comments are not part of the JSON spec.',
    E_COMMA: 'Dangling comma found.',
    W_NL_START: 'Unnecessary newlines at the start of file.',
    W_NL_END: 'Missing a new line at the end of the file.',
    W_INDENT: 'Indentation Error.',
    W_TRAILING_SPACE: 'Trailing whitespace.'
}


class CheckJsonFormat(object):
    """Test JSON for format irregularities.

        - Trailing spaces.
        - Inconsistent indentation.
        - New lines at end of file.
        - Unnecessary newlines at start of file.
        - Trailing commas.
        - Malformed JSON.
    """

    def __init__(self, use_tabs=False, allow_comments=False):
        """Setup the settings."""
        self.use_tabs = use_tabs
        self.allow_comments = allow_comments
        self.fail = False

    def index_lines(self, text):
        """Index the char range of each line."""
        self.line_range = []
        count = 1
        last = 0
        for m in re.finditer('\n', text):
            self.line_range.append((last, m.end(0) - 1, count))
            last = m.end(0)
            count += 1

    def get_line(self, pt):
        """Get the line from char index."""
        line = None
        for r in self.line_range:
            if pt >= r[0] and pt <= r[1]:
                line = r[2]
                break
        return line

    def check_comments(self, text):
        """Check for JavaScript comments.

        Log them and strip them out so we can continue.
        """
        def remove_comments(group):
            return ''.join([x[0] for x in RE_LINE_PRESERVE.findall(group)])

        def evaluate(m):
            text = ''
            g = m.groupdict()
            if g["code"] is None:
                if not self.allow_comments:
                    self.log_failure(E_COMMENTS, self.get_line(m.start(0)))
                text = remove_comments(g["comments"])
            else:
                text = g["code"]
            return text

        return ''.join(map(lambda m: evaluate(m), RE_COMMENT.finditer(text)))

    def check_dangling_commas(self, text):
        """Check for dangling commas.

        Log them and strip them out so we can continue.
        """
        def check_comma(g, m, line):
            # ,] -> ] or ,} -> }
            self.log_failure(E_COMMA, line)
            if g["square_comma"] is not None:
                return g["square_ws"] + g["square_bracket"]
            else:
                return g["curly_ws"] + g["curly_bracket"]

        def evaluate(m):
            g = m.groupdict()
            return check_comma(
                g, m, self.get_line(m.start(0))
            ) if g["code"] is None else g["code"]

        return ''.join(
            map(lambda m: evaluate(m), RE_TRAILING_COMMA.finditer(text)))

    def log_failure(self, code, line=None):
        """Log failure.

        Log failure code, line number (if available) and message.
        """
        if line:
            print("%s: Line %d - %s" % (code, line, VIOLATION_MSG[code]))
        else:
            print("%s: %s" % (code, VIOLATION_MSG[code]))
        self.fail = True

    def check_format(self, file_name):
        """Initiate teh check."""
        self.fail = False
        with codecs.open(file_name, encoding='utf-8') as f:
            count = 1
            for line in f:
                if count == 1 and line.strip() == '':
                    self.log_failure(W_NL_START, count)
                if not line.endswith('\n'):
                    self.log_failure(W_NL_END, count)
                if RE_TRAILING_SPACES.match(line):
                    self.log_failure(W_TRAILING_SPACE, count)
                if (RE_LINE_INDENT_TAB if self.use_tabs else
                        RE_LINE_INDENT_SPACE).match(line) is None:
                    self.log_failure(W_INDENT, count)
                count += 1
            f.seek(0)
            text = f.read()

        self.index_lines(text)
        text = self.check_comments(text)
        self.index_lines(text)
        text = self.check_dangling_commas(text)
        try:
            json.loads(text)
        except Exception as e:
            self.log_failure(E_MALFORMED)
            print(e)
        return self.fail


class TestSublimeResources(unittest.TestCase):
    """Test Sublime JSON resource files."""

    def _get_files(self, pattern, folder='.'):
        for root, dirnames, filenames in os.walk(folder):
            for filename in fnmatch.filter(filenames, pattern):
                yield os.path.join(root, filename)
            ignored = ('.git', '.hg', '.svn', '.tox')
            for dirname in [d for d in dirnames if d not in ignored]:
                for f in self._get_files(pattern, os.path.join(root, dirname)):
                    yield f

    def test_json(self):
        print()  # add a new line to console output before printing file names
        patterns = (
            '*.json',
            '*.sublime-commands',
            '*.sublime-keymap',
            '*.sublime-menu',
            '*.sublime-mousemap',
            '*.sublime-settings',
            '*.sublime-settings-hints',
            '*.sublime-theme'
        )
        folder = os.path.dirname(os.path.dirname(__file__))
        for pattern in patterns:
            for file in self._get_files(pattern, folder=folder):
                print("checking %s ..." % file)
                self.assertFalse(
                    CheckJsonFormat(False, True).check_format(file),
                    "%s does not comform to expected format!" % file)
