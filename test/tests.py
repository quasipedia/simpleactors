#! /usr/bin/env python
'''
Test suite for Simple Actors.
'''

import unittest
from unittest import mock

import simpleactors as sa


class ActorSingle(sa.Actor):

    @sa.on('echo')
    def echo_callback(self, message, emitter, a_dictionary):
        a_dictionary['emitter'] = emitter


class ActorDouble(sa.Actor):

    @sa.on('foo')
    @sa.on('bar')
    def double_callback(self, message, emitter, *args, **kwargs):
        pass


class ActorAny(sa.Actor):

    messages = []

    @sa.on(sa.ANY)
    def any_callback(self, message, emitter, *args, **kwargs):
        self.messages.append(message)


class BaseTest(unittest.TestCase):

    '''Base class for all tests of simpleactors.'''

    def tearDown(self):
        sa.reset()


class TestModuleFunctions(BaseTest):

    '''Tests for the module-level functions.'''

    def test_reset(self):
        '''reset() clear all registries.'''
        ActorSingle()
        self.assertTrue(len(sa.global_actors))
        self.assertTrue(len(sa.global_actors_by_id))
        self.assertTrue(len(sa.global_callbacks))
        sa.reset()
        self.assertFalse(len(sa.global_actors))
        self.assertFalse(len(sa.global_actors_by_id))
        self.assertFalse(len(sa.global_callbacks))

    def test_get_by_id_ok(self):
        '''get_by_id() return an object with a given ID by a given class.'''
        actor = sa.Actor(uid='spam')
        actual = sa.get_by_id(sa.Actor, 'spam')
        self.assertEqual(actor, actual)

    def test_get_by_id_ko(self):
        '''get_by_id() return None on "not found" results.'''
        actual = sa.get_by_id(sa.Actor, 'spam')
        self.assertEqual(None, actual)


class TestActor(BaseTest):

    '''Test suite for the Actor class.'''

    def test_not_instantiated(self):
        '''No callback is registered if the class hasn't been instantiated.'''
        self.assertFalse(sa.global_callbacks)

    def test_instantiated(self):
        '''Instantiating an actor add its callback to the global registry.'''
        actor = ActorSingle()
        self.assertTrue(actor.is_plugged)
        expected = {'echo': set([actor.echo_callback])}
        self.assertEqual(expected, sa.global_callbacks)

    def test_double_uid(self):
        '''Instantiating an actor with existing uid raises.'''
        sa.Actor(uid='foo')
        self.assertRaises(ValueError, sa.Actor, uid='foo')

    def test_instantiated_no_autoplug(self):
        '''Instantiating an actor with auto_plug set to False prevent plug.'''
        actor = ActorSingle(auto_plug=False)
        self.assertFalse(actor.is_plugged)
        expected = {}
        self.assertEqual(expected, sa.global_callbacks)

    def test_plug_save_cycles(self):
        '''Actor.plug doesn't do anything if actor.is_plugged == True.'''
        actor = ActorSingle()
        saved = sa.global_callbacks.copy()
        self.assertTrue(actor.is_plugged)
        actor.plug()
        self.assertEqual(saved, sa.global_callbacks)

    def test_unplug(self):
        '''Actor.unplug will remove all callbacks from the registry.'''
        actor = ActorSingle()
        actor.unplug()
        self.assertFalse(actor.is_plugged)
        expected = {'echo': set()}
        self.assertEqual(expected, sa.global_callbacks)

    def test_unplug_save_cycles(self):
        '''Actor.unplug doesn't do anything if actor.is_plugged == False.'''
        actor = ActorSingle()
        actor._Actor__plugged = False
        self.assertFalse(actor.is_plugged)
        actor.unplug()
        self.assertEqual({'echo': set([actor.echo_callback])},
                         sa.global_callbacks)

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

    def test_double_decorated(self):
        '''It is possible for a callback to listen to more than one message.'''
        actor = ActorDouble()
        expected = {'foo': set([actor.double_callback]),
                    'bar': set([actor.double_callback])}
        self.assertEqual(expected, sa.global_callbacks)


class TestDirector(BaseTest):

    '''Test suite for the Director class.'''

    def test_process_event(self):
        '''Processing an events means triggering all callbacks.'''
        mock_cb_one = mock.MagicMock(name='one')
        mock_cb_two = mock.MagicMock(name='two')
        mock_cb_three = mock.MagicMock(name='three')
        sa.global_callbacks['foo'] = set([mock_cb_one, mock_cb_two])
        sa.global_callbacks['bar'] = set([mock_cb_three])
        director = sa.Director()
        event = ('foo', None, (1, 2), {'spam': 42})
        director.process_event(event)
        mock_cb_one.assert_called_once_with('foo', None, 1, 2, spam=42)
        mock_cb_two.assert_called_once_with('foo', None, 1, 2, spam=42)
        self.assertFalse(mock_cb_three.called)

    def test_actors(self):
        '''Director.actors return all actors withouth the director.'''
        first = ActorSingle()
        second = ActorSingle()
        third = ActorDouble()
        director = sa.Director()
        expected = set([first, second, third])
        self.assertEqual(expected, director.actors)

    def test_run(self):
        '''A callback is triggered on emitting the bound signal.'''
        actor = ActorSingle()
        director = sa.Director()
        a_dictionary = {}
        actor.emit('echo', a_dictionary=a_dictionary)
        director.run()
        self.assertEqual({'emitter': actor}, a_dictionary)

    def test_any(self):
        '''A callback bound to sa.ANY is triggered by any signal.'''
        actor = ActorAny()
        director = sa.Director()
        actor.emit('foobar')
        director.run()
        self.assertEqual([sa.INITIATE, 'foobar'], actor.messages)

    def test_run_send_initiate_event(self):
        '''Running the Dirctor emit the INITIATE signal.'''
        director = sa.Director()
        with mock.patch.object(director, 'process_event') as mock_process:
            director.emit('second')
            director.run()
            expected = [sa.INITIATE, 'second']
            actual = [c[0][0][0] for c in mock_process.call_args_list]
            self.assertEqual(expected, actual)

    def test_run_effect_on_registries(self):
        '''Registries are left untouched by a simulation run.'''
        actor = ActorSingle()
        director = sa.Director()
        director.run()
        expected = {'echo': set([actor.echo_callback]),
                    sa.KILL: set([director.kill]),
                    sa.HALT: set([director.halt]),
                    sa.INITIATE: set(),
                    sa.ANY: set()}
        self.assertEqual(expected, sa.global_callbacks)
        self.assertEqual(set([actor, director]), sa.global_actors)
        self.assertEqual(0, len(sa.global_event_queue))

    def test_kill(self):
        '''Killing an actor removes it completely from the registries.'''
        actor = ActorSingle()
        director = sa.Director()
        actor.emit(sa.KILL, target=actor)
        director.run()
        self.assertNotIn(actor, sa.global_actors)
        self.assertNotIn(actor.echo_callback, sa.global_callbacks['echo'])

    def test_halt(self):
        '''Halting the directory process FINISH and reset the event queue.'''
        director = sa.Director()
        sa.global_event_queue.append('foo')  # If processed --> ValueError
        with mock.patch.object(director, 'process_event') as mock_process:
            director.halt(sa.HALT, self)
            self.assertEqual([], list(sa.global_event_queue))
            mock_process.assert_called_once_with((sa.FINISH, director, (), {}))
