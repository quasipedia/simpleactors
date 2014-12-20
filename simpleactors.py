#! /usr/bin/env python
'''
An experimental implementation of the Actor model with asyncio.
'''

import logging
import inspect
from collections import deque, defaultdict

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

global_actors = set()
global_event_queue = deque()
global_callbacks = defaultdict(set)

# Messages that can be emitted by Actors
ATTACH = object()
DETACH = object()
REMOVE = object()
HALT = object()
# Messages that can be emitted by Director
INTIATE = object()
FINISH = object()


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

    '''An actor that reacts to events.'''

    def __init__(self):
        global_actors.add(self)
        self._is_attached = False
        self._attach()

    def _attach(self):
        '''Edd the actor's methods to the callback registry.'''
        if self._is_attached:
            return
        for _, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, '_callback_messages'):
                for message in method._callback_messages:
                    global_callbacks[message].add(method)
        self._is_attached = True

    def emit(self, message, *args, **kwargs):
        '''Emit an event.'''
        global_event_queue.append((message, self, args, kwargs))


class Director(Actor):

    '''Orchestrate all actors.'''

    def process_event(self, event):
        message, emitter, args, kwargs = event
        for callback in global_callbacks[message]:
            callback(message, emitter, *args, **kwargs)

    def run(self):
        '''Run until there are no events to be processed.'''
        self.emit(INTIATE)
        while global_event_queue:
            self.process_event(global_event_queue.popleft())

    @on(ATTACH)
    def attach(self, event, emitter, *args, **kwargs):
        emitter._attach()

    @on(DETACH)
    def detach(self, event, emitter, *args, **kwargs):
        '''Remove the actor's methods from the callback registry.'''
        for message, callbacks in global_callbacks.items():
            if message is not ATTACH:
                callbacks.discard(emitter)

    @on(REMOVE)
    def remove(self, event, emitter, *args, **kwargs):
        self.detach(DETACH, emitter)
        global_callbacks[ATTACH].remove(emitter)
        global_actors.remove(emitter)

    @on(HALT)
    def halt(self, message, emitter, *args, **kwargs):
        '''Halt the execution of the loop.'''
        self.process_event((FINISH, self, (), {}))
        exit()
