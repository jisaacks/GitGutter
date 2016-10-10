try:
    from .git_gutter_settings import settings
except (ImportError, ValueError):
    from git_gutter_settings import settings


class ViewCollection:
    views = {} # Todo: these aren't really views but handlers. Refactor/Rename.

    @staticmethod
    def add(view):
        key = ViewCollection.get_key(view)
        try:
            from .git_gutter_handler import GitGutterHandler
        except (ImportError, ValueError):
            from git_gutter_handler import GitGutterHandler
        handler = ViewCollection.views[key] = GitGutterHandler(view)
        handler.reset()
        return handler

    @staticmethod
    def get_key(view):
        return view.file_name()

    @staticmethod
    def has_view(view):
        key = ViewCollection.get_key(view)
        return key in ViewCollection.views

    @staticmethod
    def get_handler(view):
        if ViewCollection.has_view(view):
            key = ViewCollection.get_key(view)
            return ViewCollection.views[key]
        else:
            return ViewCollection.add(view)

    @staticmethod
    def diff_line_change(view, line):
        return ViewCollection.get_handler(view).diff_line_change(line)

    @staticmethod
    def diff(view):
        return ViewCollection.get_handler(view).diff()
