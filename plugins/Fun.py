###
# Copyright (c) 2002-2004, Jeremiah Fincher
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

"""
Provides a multitude of fun, useless commands.
"""

__revision__ = '$Id$'

import supybot.plugins as plugins

import gc
import re
import sys
import md5
import sha
import random
import inspect
import mimetypes
from itertools import imap

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import wrap
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.registry as registry
import supybot.webutils as webutils
import supybot.callbacks as callbacks


conf.registerPlugin('Fun')
conf.registerGroup(conf.supybot.plugins.Fun, 'levenshtein')
conf.registerGlobalValue(conf.supybot.plugins.Fun.levenshtein, 'max',
    registry.PositiveInteger(256, """Determines the maximum size of a string
    given to the levenshtein command.  The levenshtein command uses an O(n**3)
    algorithm, which means that with strings of length 256, it can take 1.5
    seconds to finish; with strings of length 384, though, it can take 4
    seconds to finish, and with strings of much larger lengths, it takes more
    and more time.  Using nested commands, strings can get quite large, hence
    this variable, to limit the size of arguments passed to the levenshtein
    command."""))

class MyFunProxy(object):
    def reply(self, msg, s):
        self.s = s

class Fun(callbacks.Privmsg):
    def __init__(self):
        self.outFilters = ircutils.IrcDict()
        callbacks.Privmsg.__init__(self)

    def ping(self, irc, msg, args):
        """takes no arguments

        Checks to see if the bot is alive.
        """
        irc.reply('pong', prefixName=False)

    def hexip(self, irc, msg, args, ip):
        """<ip>

        Returns the hexadecimal IP for that IP.
        """
        quads = ip.split('.')
        ret = ""
        for quad in quads:
            i = int(quad)
            ret += '%02x' % i
        irc.reply(ret.upper())
    hexip = wrap(hexip, ['ip'])

    def ord(self, irc, msg, args, letter):
        """<letter>

        Returns the 8-bit value of <letter>.
        """
        irc.reply(str(ord(letter)))
    ord = wrap(ord, ['letter'])

    def chr(self, irc, msg, args, i):
        """<number>

        Returns the character associated with the 8-bit value <number>
        """
        try:
            irc.reply(chr(i))
        except ValueError:
            irc.error('That number doesn\'t map to an 8-bit character.')
    chr = wrap(chr, ['int'])

    def encode(self, irc, msg, args, encoding, text):
        """<encoding> <text>

        Returns an encoded form of the given text; the valid encodings are
        available in the documentation of the Python codecs module:
        <http://www.python.org/doc/lib/node127.html>.
        """
        try:
            irc.reply(text.encode(encoding))
        except LookupError:
            irc.errorInvalid('encoding', encoding)
    encode = wrap(encode, ['something', 'text'])

    def decode(self, irc, msg, args, encoding, text):
        """<encoding> <text>

        Returns an un-encoded form of the given text; the valid encodings are
        available in the documentation of the Python codecs module:
        <http://www.python.org/doc/lib/node127.html>.
        """
        try:
            irc.reply(text.decode(encoding).encode('utf-8'))
        except LookupError:
            irc.errorInvalid('encoding', encoding)
    decode = wrap(decode, ['something', 'text'])

    def xor(self, irc, msg, args, password, text):
        """<password> <text>

        Returns <text> XOR-encrypted with <password>.  See
        http://www.yoe.org/developer/xor.html for information about XOR
        encryption.
        """
        passwordlen = len(password)
        i = 0
        ret = []
        for c in text:
            ret.append(chr(ord(c) ^ ord(password[i])))
            i = (i + 1) % passwordlen
        irc.reply(''.join(ret))
    xor = wrap(xor, ['something', 'text'])

    def mimetype(self, irc, msg, args, filename):
        """<filename>

        Returns the mime type associated with <filename>
        """
        (type, encoding) = mimetypes.guess_type(filename)
        if type is not None:
            irc.reply(type)
        else:
            s = 'I couldn\'t figure out that filename.'
            irc.reply(s)
    mimetype = wrap(mimetype, ['something'])

    def md5(self, irc, msg, args, text):
        """<text>

        Returns the md5 hash of a given string.  Read
        http://www.rsasecurity.com/rsalabs/faq/3-6-6.html for more information
        about md5.
        """
        irc.reply(md5.md5(text).hexdigest())
    md5 = wrap(md5, ['text'])

    def sha(self, irc, msg, args, text):
        """<text>

        Returns the SHA hash of a given string.  Read
        http://www.secure-hash-algorithm-md5-sha-1.co.uk/ for more information
        about SHA.
        """
        irc.reply(sha.sha(text).hexdigest())
    sha = wrap(sha, ['text'])

    def urlquote(self, irc, msg, args, text):
        """<text>

        Returns the URL quoted form of the text.
        """
        irc.reply(webutils.urlquote(text))
    urlquote = wrap(urlquote, ['text'])

    def urlunquote(self, irc, msg, args, text):
        """<text>

        Returns the text un-URL quoted.
        """
        s = webutils.urlunquote(text)
        irc.reply(s)
    urlunquote = wrap(urlunquote, ['text'])

    def coin(self, irc, msg, args):
        """takes no arguments

        Flips a coin and returns the result.
        """
        if random.randrange(0, 2):
            irc.reply('heads')
        else:
            irc.reply('tails')
    coin = wrap(coin)

    def dice(self, irc, msg, args, m):
        """<dice>d<sides>

        Rolls a die with <sides> number of sides <dice> times.
        For example, 2d6 will roll 2 six-sided dice; 10d10 will roll 10
        ten-sided dice.
        """
        (dice, sides) = imap(int, m.groups())
        if dice > 6:
            irc.error('You can\'t roll more than 6 dice.')
        elif sides > 100:
            irc.error('Dice can\'t have more than 100 sides.')
        else:
            L = [0] * dice
            for i in xrange(dice):
                L[i] = random.randrange(1, sides+1)
            irc.reply(utils.commaAndify([str(x) for x in L]))
    _dicere = re.compile(r'^(\d+)d(\d+)$')
    dice = wrap(dice, [('matches', _dicere,
                        'Dice must be of the form <dice>d<sides>')])

    def objects(self, irc, msg, args):
        """takes no arguments

        Returns the number and types of Python objects in memory.
        """
        classes = 0
        functions = 0
        modules = 0
        strings = 0
        dicts = 0
        lists = 0
        tuples = 0
        refcounts = 0
        objs = gc.get_objects()
        for obj in objs:
            if isinstance(obj, str):
                strings += 1
            if isinstance(obj, tuple):
                tuples += 1
            elif inspect.isroutine(obj):
                functions += 1
            elif isinstance(obj, dict):
                dicts += 1
            elif isinstance(obj, list):
                lists += 1
            elif inspect.isclass(obj):
                classes += 1
            elif inspect.ismodule(obj):
                modules += 1
            refcounts += sys.getrefcount(obj)
        response = 'I have %s objects: %s modules, %s classes, %s functions, '\
                   '%s dictionaries, %s lists, %s tuples, %s strings, and a ' \
                   'few other odds and ends.  ' \
                   'I have a total of %s references.' % \
                   (len(objs), modules, classes, functions,
                    dicts, lists, tuples, strings, refcounts)
        irc.reply(response)
    objects = wrap(objects)

    def levenshtein(self, irc, msg, args, s1, s2):
        """<string1> <string2>

        Returns the levenshtein distance (also known as the "edit distance"
        between <string1> and <string2>)
        """
        max = self.registryValue('levenshtein.max')
        if len(s1) > max or len(s2) > max:
            irc.error('Levenshtein distance is a complicated algorithm, try '
                      'it with some smaller inputs.')
        else:
            irc.reply(str(utils.distance(s1, s2)))
    levenshtein = wrap(levenshtein, ['text', 'text'])

    def soundex(self, irc, msg, args, text, length):
        """<string> [<length>]

        Returns the Soundex hash to a given length.  The length defaults to
        4, since that's the standard length for a soundex hash.  For unlimited
        length, use 0.
        """
        irc.reply(utils.soundex(text, length))
    soundex = wrap(soundex, ['text', ('?int', 4)])

    # The list of words and algorithm are pulled straight the mozbot
    # MagicEightBall.bm module: http://tinyurl.com/7ytg7
    _responses = {'positive': ['It is possible.', 'Yes!', 'Of course.', 
                               'Naturally.', 'Obviously.', 'It shall be.',
                               'The outlook is good.', 'It is so.',
                               'One would be wise to think so.', 
                               'The answer is certainly yes.'],
                  'negative': ['In your dreams.', 'I doubt it very much.',
                               'No chance.', 'The outlook is poor.', 
                               'Unlikely.', 'About as likely as pigs flying.',
                               'You\'re kidding, right?', 'NO!', 'NO.', 'No.', 
                               'The answer is a resounding no.', ],
                  'unknown' : ['Maybe...', 'No clue.', '_I_ don\'t know.', 
                               'The outlook is hazy, please ask again later.', 
                               'What are you asking me for?', 'Come again?',
                               'You know the answer better than I.', 
                               'The answer is def-- oooh! shiny thing!'],
                 }
    
    def _checkTheBall(self, questionLength):
        if questionLength % 3 == 0:
            category = 'positive'
        elif questionLength % 3 == 1:
            category = 'negative'
        else:
            category = 'unknown'
        return random.choice(self._responses[category])

    def eightball(self, irc, msg, args, text):
        """[<question>]

        Ask a question and the answer shall be provided.
        """
        if text:
            irc.reply(self._checkTheBall(len(text)))
        else:
            irc.reply(self._checkTheBall(random.randint(0, 2)))
    eightball = wrap(eightball, ['?text'])

    _rouletteChamber = random.randrange(0, 6)
    _rouletteBullet = random.randrange(0, 6)
    def roulette(self, irc, msg, args, spin):
        """[spin]

        Fires the revolver.  If the bullet was in the chamber, you're dead.
        Tell me to spin the chambers and I will.
        """
        if spin:
            self._rouletteBullet = random.randrange(0, 6)
            irc.reply('*SPIN* Are you feeling lucky?', prefixName=False)
            return
        channel = msg.args[0]
        if self._rouletteChamber == self._rouletteBullet:
            self._rouletteBullet = random.randrange(0, 6)
            self._rouletteChamber = random.randrange(0, 6)
            if irc.nick in irc.state.channels[channel].ops:
                irc.queueMsg(ircmsgs.kick(channel, msg.nick, 'BANG!'))
            else:
                irc.reply('*BANG* Hey, who put a blank in here?!',
                          prefixName=False)
            irc.reply('reloads and spins the chambers.', action=True)
        else:
            irc.reply('*click*')
            self._rouletteChamber += 1
            self._rouletteChamber %= 6
    roulette = wrap(roulette, ['public', ('?literal', False, 'spin')])

    def monologue(self, irc, msg, args, channel):
        """[<channel>]

        Returns the number of consecutive lines you've sent in <channel>
        without being interrupted by someone else (i.e. how long your current
        'monologue' is).  <channel> is only necessary if the message isn't sent
        in the channel itself.
        """
        i = 0
        for m in reversed(irc.state.history):
            if m.command != 'PRIVMSG':
                continue
            if not m.prefix:
                continue
            if not ircutils.strEqual(m.args[0], channel):
                continue
            if msg.prefix == m.prefix:
                i += 1
            else:
                break
        iS = utils.nItems('line', i)
        irc.reply('Your current monologue is at least %s long.' % iS)
    monologue = wrap(monologue, ['channel'])


Class = Fun

# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
