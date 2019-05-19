# -*- coding: utf-8 -*-
import traceback

from queue import Empty
from queue import Queue
from threading import Thread

from .promise import Promise


class Task(object):

    """
    Task runs a python function `target` when called.
    """

    def __init__(self, target, *args, **kwargs):
        """Initialize the Task object."""
        self.target = target
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.target(*self.args, **self.kwargs)


class TaskQueue(Thread):

    """
    A background thread to start all queued processes one after another.
    """

    def __init__(self):
        super().__init__(daemon=True)
        self.queue = Queue()
        self.active_task = None
        self.running = False

    def __del__(self):
        self.running = False

    def execute(self, task):
        self.queue.put(task)

    def cancel_all(self):
        try:
            while not self.Empty():
                self.queue.get_nowait()
                self.queue.task_done()
        except Empty:
            pass

    def busy(self):
        result = False
        with self._block:
            result = self.active_task is not None
        return result

    def run(self):
        self.running = True
        while self.running:
            task = self.queue.get()
            with self._block:
                self.active_task = task
            try:
                task.run()
            except:
                traceback.print_exc()
            finally:
                self.queue.task_done()
                with self._block:
                    self.active_task = None


_tasks = TaskQueue()
_tasks.start()


def busy():
    return _tasks.busy()


def execute_async(func, *args, **kwargs):
    return Promise(lambda resolve_fn: _tasks.execute(
        Task(func, resolve_fn, *args, **kwargs)))


def cancel_all():
    _tasks.cancel_all()
