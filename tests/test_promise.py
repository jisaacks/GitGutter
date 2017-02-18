"""
Tests for Promise.

To run this unit test install UnitTesting package and choose
"UnitTesting: Test current project" command.
"""

import sys
from os import path
import time
from unittest import TestCase

import sublime

sys.path.append(path.dirname(path.dirname(__file__)))
from modules.promise import Promise


class test_promise(TestCase):
    # Tests are using private methods of Promise on purpose.

    def test_chain_with_resolved(self):
        def worker(resolve_fn):
            resolve_fn(999)

        def assertResult(result):
            self.assertEqual(result, 999)

        promise = Promise(worker)
        self.assertTrue(promise._is_resolved())
        promise2 = promise.then(assertResult)
        self.assertTrue(promise2._is_resolved())

    def test_chain_with_pending(self):
        def worker_async(resolve_fn):
            sublime.set_timeout_async(lambda: resolve_fn(999), 100)

        def assertResult(result):
            self.assertEqual(result, 999)

        promise = Promise(worker_async)
        self.assertFalse(promise._is_resolved())
        promise2 = promise.then(assertResult)
        self.assertFalse(promise2._is_resolved())
        # Let promises resolve.
        time.sleep(0.2)
        self.assertTrue(promise._is_resolved())

    def test_promise_resolve(self):
        promise = Promise.resolve(999)
        self.assertTrue(promise._is_resolved())
        self.assertEqual(promise._get_value(), 999)

    def test_chain_with_promise(self):
        def worker_async(resolve_fn):
            sublime.set_timeout_async(lambda: resolve_fn(999), 100)

        def worker_async2(resolve_fn):
            sublime.set_timeout_async(lambda: resolve_fn(888), 100)

        def callback(async_value):
            self.assertEqual(async_value, 999)
            return Promise(worker_async2)

        def verify_async2_value(value):
            self.assertEqual(value, 888)

        promise = Promise(worker_async)
        self.assertFalse(promise._is_resolved())
        promise2 = promise.then(callback)
        self.assertFalse(promise2._is_resolved())
        promise2.then(verify_async2_value)
        # Let both promises resolve.
        time.sleep(0.500)
        self.assertTrue(promise._is_resolved())
        self.assertEqual(promise._get_value(), 999)
        self.assertTrue(promise2._is_resolved())
        self.assertEqual(promise2._get_value(), 888)
