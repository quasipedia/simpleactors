#! /usr/bin/env python3
'''
A guessing number simulator.
'''

from random import randint

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
    def give_hint(self, message, emitter, guess):
        # The following construct is the equivalent of the python2 `cmp`
        # function, as cmp(a, b) == (a > b) - (a < b)
        hint = (guess > self.secret) - (guess < self.secret)
        self.emit('hint', number=guess, hint=hint)
        print('your guess was {}'.format(HUMAN_CMP[hint]))


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
                return print('CodeBreaker celebrates in joy!')
        self.make_attempt()

    def make_attempt(self):
        guess = randint(self.min, self.max)
        self.emit('attempt', guess=guess)
        print('I am guessing {}'.format(guess))


if __name__ == '__main__':
    # Since a reference to all instantiated Actors is kept in the simpleactors
    # module registry, there's no reason to keep track of the instances here.
    #     Not having a reference in the main code is even better if the `KILL`
    # message is given somewhere, as this will instantly cause the killed actor
    # to be garbage collected.
    CodeKeeper(), CodeBreaker()
    Director().run()
