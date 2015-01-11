#! /usr/bin/env python
'''
An simple implementation of the Actor model.
'''

import logging
import inspect
from collections import deque, defaultdict

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

global_actors = set()
global_actors_by_id = defaultdict(dict)
global_event_queue = deque()
global_callbacks = defaultdict(set)

# Messages that can be emitted by Actors
KILL = object()  # Kill an actor
HALT = object()  # Halt the main loop

# Messages that can be emitted by Director
INITIATE = object()  # First action when the loop starts
FINISH = object()  # Las action before the loop ends

# Special on values
ANY = object()  # @on(ANY) trigger for any message


def reset():
    '''Reset simpleactors global registries.'''
    global_actors.clear()
    global_actors_by_id.clear()
    global_event_queue.clear()
    global_callbacks.clear()


def get_by_id(class_, uid):
    '''Return an object by it's id'''
    return global_actors_by_id[class_].get(uid, None)


def on(message):
    '''Decorator that register a class method as callback for a message.'''
    def decorator(function):
        try:
            function._callback_messages.append(message)
        except AttributeError:
            function._callback_messages = [message]
        return function
    return decorator


class Actor:

    '''An actor that reacts to events.

    Args:
        auto_plug - if True (default) the actor will automatically plug itself
                    into the mail event loop.
    '''

    def __init__(self, uid=None, auto_plug=True):
        self.id = id(self) if uid is None else uid
        global_actors.add(self)
        if self.id in global_actors_by_id[self.__class__]:
            msg = 'A "{}" instance with id "{}" has been already created.'
            raise ValueError(msg.format(self.__class__, self.id))
        global_actors_by_id[self.__class__][self.id] = self
        self.__plugged = False
        if auto_plug:
            self.plug()

    def plug(self):
        '''Add the actor's methods to the callback registry.'''
        if self.__plugged:
            return
        for _, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, '_callback_messages'):
                for message in method._callback_messages:
                    global_callbacks[message].add(method)
        self.__plugged = True

    def unplug(self):
        '''Remove the actor's methods from the callback registry.'''
        if not self.__plugged:
            return
        members = set([method for _, method
                      in inspect.getmembers(self, predicate=inspect.ismethod)])
        for message in global_callbacks:
            global_callbacks[message] -= members
        self.__plugged = False

    @property
    def is_plugged(self):
        '''Return True if the actor is listening for messages.'''
        return self.__plugged

    def emit(self, message, *args, **kwargs):
        '''Emit an event.'''
        global_event_queue.append((message, self, args, kwargs))


class Director(Actor):

    '''Orchestrate all actors.'''

    def process_event(self, event):
        message, emitter, args, kwargs = event
        for callback in global_callbacks[message]:
            callback(message, emitter, *args, **kwargs)
        for callback in global_callbacks[ANY]:
            callback(message, emitter, *args, **kwargs)

    def run(self):
        '''Run until there are no events to be processed.'''
        # We left-append rather than emit (right-append) because some message
        # may have been already queued for execution before the director runs.
        global_event_queue.appendleft((INITIATE, self, (), {}))
        while global_event_queue:
            self.process_event(global_event_queue.popleft())

    @property
    def actors(self):
        ret = global_actors.copy()
        ret.remove(self)
        return ret

    @on(KILL)
    def kill(self, event, emitter, target, **kwargs):
        target.unplug()
        global_actors.remove(target)

    @on(HALT)
    def halt(self, message, emitter, *args, **kwargs):
        '''Halt the execution of the loop.'''
        self.process_event((FINISH, self, (), {}))
        global_event_queue.clear()
