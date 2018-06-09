# -*- coding: utf-8 -*-
import codecs

import sublime

from .temp import TempFile

# The view class has a method called 'change_count()'
_HAVE_VIEW_CHANGE_COUNT = hasattr(sublime.View, 'change_count')

ENCODING_MAP = {
    'UTF-8': 'utf-8',
    'UTF-8 with BOM': 'utf-8-sig',
    'UTF-16 LE': 'utf-16-le',
    'UTF-16 LE with BOM': 'utf-16',
    'UTF-16 BE': 'utf-16-be',
    'UTF-16 BE with BOM': 'utf-16',
    'Western (Windows 1252)': 'cp1252',
    'Western (ISO 8859-1)': 'iso8859-1',
    'Western (ISO 8859-3)': 'iso8859-3',
    'Western (ISO 8859-15)': 'iso8859-15',
    'Western (Mac Roman)': 'mac-roman',
    'DOS (CP 437)': 'cp437',
    'Arabic (Windows 1256)': 'cp1256',
    'Arabic (ISO 8859-6)': 'iso8859-6',
    'Baltic (Windows 1257)': 'cp1257',
    'Baltic (ISO 8859-4)': 'iso8859-4',
    'Celtic (ISO 8859-14)': 'iso8859-14',
    'Central European (Windows 1250)': 'cp1250',
    'Central European (ISO 8859-2)': 'iso8859-2',
    'Cyrillic (Windows 1251)': 'cp1251',
    'Cyrillic (Windows 866)': 'cp866',
    'Cyrillic (ISO 8859-5)': 'iso8859-5',
    'Cyrillic (KOI8-R)': 'koi8-r',
    'Cyrillic (KOI8-U)': 'koi8-u',
    'Estonian (ISO 8859-13)': 'iso8859-13',
    'Greek (Windows 1253)': 'cp1253',
    'Greek (ISO 8859-7)': 'iso8859-7',
    'Hebrew (Windows 1255)': 'cp1255',
    'Hebrew (ISO 8859-8)': 'iso8859-8',
    'Nordic (ISO 8859-10)': 'iso8859-10',
    'Romanian (ISO 8859-16)': 'iso8859-16',
    'Turkish (Windows 1254)': 'cp1254',
    'Turkish (ISO 8859-9)': 'iso8859-9',
    'Vietnamese (Windows 1258)': 'cp1258',
}


class GitGutterViewCache(TempFile):

    def __init__(self, view):
        """Initialize a GitGutterViewCache object."""
        TempFile.__init__(self, mode='wb')
        # tha attached view
        self.view = view
        # last view change count
        self._change_count = -1
        # the text size
        self._size = None
        # the text content
        self._text = None

    def __getitem__(self, arg):
        if isinstance(arg, sublime.Region):
            return self.text[arg.begin():arg.end()]
        else:
            return self.text[arg]

    @property
    def size(self):
        """Return the number of characters in the view."""
        if self._size is None:
            self._size = self.view.size()
        return self._size

    @property
    def text(self):
        """Return the text content of the view."""
        if self._text is None:
            self._text = self.view.substr(sublime.Region(0, self.size))
        return self._text

    def invalidate(self):
        """Reset change_count and force writing the view cache file.

        The view content is written to a temporary file for use with git diff,
        if the view.change_count() has changed. This method forces the update
        on the next call of update_view_file().
        """
        self._change_count = -1
        self._size = None
        self._text = None

    def is_changed(self):
        """Check whether the content of the view changed."""
        return (
            _HAVE_VIEW_CHANGE_COUNT and
            self._change_count != self.view.change_count()
        )

    def update(self):
        """Write view's content to a temporary file as source for git diff.

        The file is updated only if the view.change_count() has changed to
        reduce the number of required disk writes.

        Returns:
            bool: True indicates updated file.
                  False is returned if file is up to date.
        """
        # check change counter if exists
        change_count = 0
        if _HAVE_VIEW_CHANGE_COUNT:
            # write view buffer to file only, if changed
            change_count = self.view.change_count()
            if self._change_count == change_count:
                return False

        # invalidate internal cache
        self.invalidate()

        # Try conversion
        encoding = self.python_friendly_encoding()
        try:
            encoded = self.text.encode(encoding)
        except (LookupError, UnicodeError):
            # Fallback to utf8-encoding
            encoded = self.text.encode('utf-8')

        # Write the encoded content to file
        try:
            with self as file:
                if encoding == 'utf-8-sig':
                    file.write(codecs.BOM_UTF8)
                file.write(encoded)
        except OSError as error:
            print('GitGutter failed to create view cache: %s' % error)
            return False

        # Update internal change counter after job is done
        self._change_count = change_count
        return True

    def python_friendly_encoding(self):
        """Read view encoding and transform it for use with python.

        This method reads `origin_encoding` used by ConvertToUTF8 plugin and
        goes on with ST's encoding setting if required. The encoding is
        transformed to work with python's `codecs` module.

        Returns:
            string: python compatible view encoding
        """
        encoding = self.view.settings().get('origin_encoding')
        if not encoding:
            encoding = self.view.encoding()
            if encoding == 'Undefined':
                encoding = self.view.settings().get('default_encoding', '')
            return ENCODING_MAP.get(encoding, 'utf-8')
        return encoding.replace(' ', '')
