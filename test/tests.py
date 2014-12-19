#! /usr/bin/env python
'''
Test suite for Simple Actors
'''

import unittest
from collections import deque, defaultdict

import simpleactors as sa


class DummyActor(sa.Actor):

    @sa.on('foo')
    def foo_callback(self, message, emitter, *args, **kwargs):
        pass


class BaseTest(unittest.TestCase):

    '''Base class for all tests of simpleactors.'''

    def tearDown(self):
        sa.global_actors = []
        sa.global_event_queue = deque()
        sa.global_callbacks = defaultdict(list)


class TestActor(BaseTest):

    '''Test suite for the Actor class.'''

    def test_not_instanciated(self):
        '''No callback is registered if the class hasn't been instanciated.'''
        self.assertFalse(sa.global_callbacks)

    def test_add_to_callbacks(self):
        actor = DummyActor()
        expected = [('foo', [actor.foo_callback])]
        self.assertEqual(expected, list(sa.global_callbacks.items()))
