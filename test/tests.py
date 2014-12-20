#! /usr/bin/env python
'''
Test suite for Simple Actors
'''

import unittest
from unittest import mock
from collections import deque, defaultdict

import simpleactors as sa


class ActorSingle(sa.Actor):

    @sa.on('echo')
    def foo_callback(self, message, emitter, *args, **kwargs):
        kwargs['ret_value'] = 'spam'


class ActorDouble(sa.Actor):

    @sa.on('foo')
    @sa.on('bar')
    def double_callback(self, message, emitter, *args, **kwargs):
        pass


class BaseTest(unittest.TestCase):

    '''Base class for all tests of simpleactors.'''

    def tearDown(self):
        sa.global_actors = set()
        sa.global_event_queue = deque()
        sa.global_callbacks = defaultdict(set)


class TestActor(BaseTest):

    '''Test suite for the Actor class.'''

    def test_not_instanciated(self):
        '''No callback is registered if the class hasn't been instantiated.'''
        self.assertFalse(sa.global_callbacks)

    def test_add_to_callbacks(self):
        '''Intantiating an actor add its callback to the global registry.'''
        actor = ActorSingle()
        expected = {'echo': set([actor.foo_callback])}
        self.assertEqual(expected, sa.global_callbacks)

    def test_double_decorated(self):
        '''It is possible to double-decorate a callback.'''
        actor = ActorDouble()
        expected = {'foo': set([actor.double_callback]),
                    'bar': set([actor.double_callback])}
        self.assertEqual(expected, sa.global_callbacks)

    def test_emit_appends(self):
        '''Emitting an event will append it to the global deque.'''
        sa.global_event_queue.append('scrap-me')
        actor = ActorSingle()
        actor.emit('spam')
        self.assertTrue('spam', sa.global_event_queue[1])

    def test_emit_payload(self):
        '''Emitting an event append the correct payload.'''
        actor = ActorSingle()
        actor.emit('spam', 42, foo='bar')
        expected = ('spam', self.test_emit_payload, (42, ), {'foo': 'bar'})
        self.assertTrue(expected, sa.global_event_queue[0])


class TestDirector(BaseTest):

    '''Test suite for the Director class.'''

    def test_run_send_initiate_event(self):
        '''Running the Dirctor emit the INITIATE signal.'''
        director = sa.Director()
        with mock.patch.object(director, 'emit') as mock_emit:
            director.run()
            mock_emit.assert_called_once_with(sa.INITIATE)

    def test_halt(self):
        '''Halting the directory process FINISH and reset the event queue.'''
        director = sa.Director()
        sa.global_event_queue.append('foo')
        with mock.patch.object(director, 'process_event') as mock_process:
            director.halt(sa.HALT, self)
            self.assertEqual([], list(sa.global_event_queue))
            mock_process.assert_called_once_with((sa.FINISH, director, (), {}))


class TestMessageHandling(BaseTest):

    '''Test that messages are handled properly.'''

    def test_callback_triggered(self):
        '''A callback is triggered on emitting the bound signal'''
        actor = ActorSingle()
        director = sa.Director()
        test_dict = {'ret_value': None}
        actor.emit('echo', self, (), test_dict)
        director.run()
        self.assertEqual('spam', test_dict['ret_value'])
