#! /usr/bin/env python
'''
An experimental implementation of the Actor model with asyncio.
'''

import logging
import inspect
from collections import deque, defaultdict

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

global_actors = []
global_event_queue = deque()
global_callbacks = defaultdict(list)


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
        global_actors.append(self)
        self._extract_from_decorated()

    def _extract_from_decorated(self):
        '''Extract the callback message from the function objects.'''
        for _, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, '_callback_messages'):
                for message in method._callback_messages:
                    global_callbacks[message].append(method)

    @on('foo.bar.baz')
    def foo(self, message, emitter, *args, **kwargs):
        print(message, emitter, args, kwargs)

    def emit(self, message, *args, **kwargs):
        '''Emit an event.'''
        global_event_queue.append((message, self, args, kwargs))


class Stage:

    '''Orchestrate all actors.'''

    def process_event(self, event):
        message, emitter, args, kwargs = event
        for callback in global_callbacks[message]:
            callback(message, emitter, *args, **kwargs)

    def run(self):
        '''Run until there are no events to be processed.'''
        while global_event_queue:
            self.process_event(global_event_queue.popleft())


def main():
    Actor()
    stage = Stage()
    global_event_queue.append(('foo.bar.baz', 'Mr.X', (), {}))
    stage.run()

if __name__ == '__main__':
    main()
