# import sublime_plugin

# import time
# import threading
# from functools import partial
# from collections import namedtuple


# class TimeoutThread(threading.Thread):

#     """TODOC"""

#     should_stop = False
#     last_poke = 0

#     _IdentData = namedtuple("_IdentData", "call_time callback args kwargs")

#     def __init__(self, sleep=0.1, default_ident=None, default_timeout=None,
#                  default_callback=None, *args, **kwargs):
#         super(TimeoutThread, self).__init__(*args, **kwargs)

#         self.sleep = sleep
#         self.default_ident = default_ident
#         self.default_timeout = default_timeout
#         self.default_callback = default_callback

#         self.ident_map = {}
#         self.lock = threading.Lock()

#     def run(self):
#         while not self.should_stop:
#             time.sleep(self.sleep)

#             if not self.ident_map:
#                 continue

#             # Defer callbacks to call so that we acquire the lock for as little
#             # time as necessary.
#             to_call = {}

#             with self.lock:
#                 for ident, data in self.ident_map.items():
#                     if data.call_time < time.time():
#                         to_call[ident] = data

#                 for key in to_call:
#                     del self.ident_map[key]

#             # Run in another thread?
#             for data in to_call.values():
#                 data.callback(*data.args, **data.kwargs)

#     def queue_stop(self):
#         """Set a flag to signal the desire of termination.
#         """
#         self.should_stop = True

#     def poke(self, ident=None, timeout=None, callback=None, args=[], kwargs={}):
#         """TODOC"""
#         ident = ident or self.default_ident
#         timeout = timeout or self.default_timeout
#         callback = callback or self.default_callback
#         if timeout is None:
#             raise ValueError(
#                 "Must provide timeout since no default has been set")
#         if callback is None:
#             raise ValueError(
#                 "Must provide callback since no default has been set")

#         data = self._IdentData(time.time() + timeout, callback, args, kwargs)

#         with self.lock:
#             self.ident_map[ident] = data


# # Global reference to our thread
# defer_thread = None


# def selection_callback(view):
#     print("selection timeout", view.id(), time.time())


# def modified_callback(view):
#     print("modified timeout", view.id(), time.time())


# class SelectionListener(sublime_plugin.EventListener):

#     def on_selection_modified(self, view):
#         if not view.settings().get('is_widget'):
#             defer_thread.poke(view.id(), 0.6, partial(selection_callback, view))

#     def on_modified(self, view):
#         if not view.settings().get('is_widget'):
#             # "Ident" needs to be different from the selection callback,
#             # so we just use the negative view id.
#             # The usual way would be to create a string.
#             defer_thread.poke(-view.id(), callback=modified_callback,
#                               args=[view])


# def plugin_loaded():
#     global defer_thread  # to bad nonlocal only works for non-global variables
#     defer_thread = TimeoutThread(0.1, default_timeout=0.6)
#     defer_thread.start()


# def plugin_unloaded():
#     defer_thread.queue_stop()
