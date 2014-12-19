#! /usr/bin/env python
'''
Test suite for Simple Actors
'''

import unittest
from collections import deque, defaultdict

import simpleactors as sa


class DummyActorOne(sa.Actor):

    @sa.on('foo')
    def foo_callback(self, message, emitter, *args, **kwargs):
        pass


class DummyActorTwo(sa.Actor):

    @sa.on('foo')
    @sa.on('bar')
    def double_callback(self, message, emitter, *args, **kwargs):
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
        '''No callback is registered if the class hasn't been instantiated.'''
        self.assertFalse(sa.global_callbacks)

    def test_add_to_callbacks(self):
        '''Intantiating an actor add its callback to the global registry.'''
        actor = DummyActorOne()
        expected = {'foo': [actor.foo_callback]}
        self.assertEqual(expected, sa.global_callbacks)

    def test_double_decorated(self):
        '''It is possible to double-decorate a callback.'''
        actor = DummyActorTwo()
        expected = {'foo': [actor.double_callback],
                    'bar': [actor.double_callback]}
        self.assertEqual(expected, sa.global_callbacks)

    def test_emit_appends(self):
        '''Emitting an event will append it to the global deque.'''
        sa.global_event_queue.append('scrap-me')
        actor = DummyActorOne()
        actor.emit('spam')
        self.assertTrue('spam', sa.global_event_queue[1])

    def test_emit_payload(self):
        '''Emitting an event append the correct payload.'''
        actor = DummyActorOne()
        actor.emit('spam', 42, foo='bar')
        expected = ('spam', self.test_emit_payload, (42, ), {'foo': 'bar'})
        self.assertTrue(expected, sa.global_event_queue[0])
