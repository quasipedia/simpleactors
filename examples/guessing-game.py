#! /usr/bin/env python3
'''
An guessing number simulator.
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
        self.emit('code.ready')
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
        print('CodeBreaker is ready...')

    @on('code.ready')
    @on('hint')
    # Note that make guess is the callback for two different messages, but the
    # estimate correction only happens if the message contained an hint.
    # (this is why `number` and `hint` defaults to None, btw...)
    #     Also: this is not the most pythonic way, but I wanted to show the use
    # of the double decoration.
    def make_guess(self, message, emitter, number=None, hint=None):
        if message == 'hint':
            if hint < 0:
                self.min = number
            elif hint > 0:
                self.max = number
            else:
                print('CodeBreaker celebrates in joy!')
                return
        # The following lines are executed regardless of what message triggered
        # the callback.
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
