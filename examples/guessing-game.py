#! /usr/bin/env python3
'''
A guessing number simulator.
'''

from random import randint
from time import time

from simpleactors import on, Actor, Director, INITIATE

LIMITS = 0, 100000
HUMAN_CMP = {
    -1: 'TOO LOW',
    0: 'THE SECRET CODE!',
    1: 'TOO HIGH',
}


class CodeKeeper(Actor):

    @on(INITIATE)
    def init(self, message, emitter):
        self.secret = randint(*LIMITS)
        print('CodeKeeper is ready... [secret is {}!]'.format(self.secret))

    @on('attempt')
    def give_hint(self, message, emitter, attempt):
        # The following construct is the equivalent of the python2 `cmp`
        # function, as cmp(a, b) == (a > b) - (a < b)
        hint = (attempt > self.secret) - (attempt < self.secret)
        self.emit('hint', number=attempt, hint=hint)
        print('your attempt was {}'.format(HUMAN_CMP[hint]))
        if hint == 0:
            self.emit('game.over')


class CodeBreaker(Actor):

    @on(INITIATE)
    def init(self, message, emitter):
        self.min, self.max = LIMITS
        # Since messages are processed for all actors at once, we can be sure
        # that even if the CodeBreaker gets initiated befrore the CodeKeeper
        # the CodeKeeper will have been initialised by the time the guess will
        # be processed.
        self.make_attempt()

    @on('hint')
    def adjust_limits(self, message, emitter, number, hint):
        if message == 'hint':
            if hint < 0:
                self.min = number
            elif hint > 0:
                self.max = number
            else:
                return  # Won't make an attempt if it guessed correctly
        self.make_attempt()

    def make_attempt(self):
        attempt = randint(self.min, self.max)
        self.emit('attempt', attempt=attempt)
        print('I am guessing {}'.format(attempt))


class Referee(Actor):

    @on(INITIATE)
    def init(self, message, emitter):
        self.start_time = time()
        self.msg_count = 0

    @on('attempt')
    @on('hint')
    # See? You can stack multiple decorators for the same callback! :)
    def count(self, message, emitter, *args, **kwargs):
        self.msg_count += 1

    @on('game.over')
    def stats(self, message, emitter):
        elapsed_time = time() - self.start_time
        msg = 'REFEREE: The game took {} messages and {:.3} ms to complete'
        print(msg.format(self.msg_count, elapsed_time * 1000))

if __name__ == '__main__':
    # Since a reference to all instantiated Actors is kept in the simpleactors
    # module registry, there's no reason to keep track of the instances here.
    #     Not having a reference in the main code is even better if the `KILL`
    # message is given somewhere, as this will instantly cause the killed actor
    # to be garbage collected.
    CodeKeeper(), CodeBreaker(), Referee()
    Director().run()
