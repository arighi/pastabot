#!/usr/bin/env python
#
# Twitch chat bot to interact with a LEGO Mindstorm EV3 robot.

import os
import sys
import re
from twitchio.ext import commands
from espeak import espeak
from time import time
from socket import *

from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
from chatterbot.trainers import ChatterBotCorpusTrainer

from profanity_filter import ProfanityFilter

# Twitch login token is defined in cred.py
from cred import TOKEN

### Bot settings ###

# Twitch identity / channel
CHANNEL="arighi_violin"
BOT_USER="the_pastabot"
BOT_KEYWORD = 'pastabot'

# Port used by the server (LEGO Mindstorm EV3 robot)
BOT_SERVER_PORT = 3636

# Cooldown between a response and another
BOT_COOLDOWN_SEC = 10

# Bot responses can trigger other responses if keyword is present
PASTACEPTION = True

# True: use external robot speaker, False: use PC speaker
ROBOT_SPEAKER=True

# Set to True to re-run the chat bot training
REDO_TRAINING = False

# Main chat bot class
class Bot(commands.Bot):
    def __init__(self):
        # Initialize communication with robot
        self._init_server()

        # Initialize voice
        espeak.set_voice("en-us")

        # Initialize chat bot
        self.pf = ProfanityFilter()
        self.pf.censor_char = '`'
        self.pf.extra_profane_word_dictionaries = {
                    'en': {
                        'idiot', 'stupid', 'ass', 'die', 'crazy',
                        'immortal', 'cancer',
                     }}
        self.bot = ChatBot('pastabot')
        if REDO_TRAINING:
            trainer = ChatterBotCorpusTrainer(self.bot)
            trainer.train(
                "chatterbot.corpus.english.greetings",
                "chatterbot.corpus.english.conversations",
                "chatterbot.corpus.english.emotion",
                "chatterbot.corpus.english.psychology",
                "chatterbot.corpus.english.science",
                "chatterbot.corpus.english.food",
                "chatterbot.corpus.english.computers",
                "chatterbot.corpus.english.humor",
                "chatterbot.corpus.english.health",
                "chatterbot.corpus.english.ai",
                "chatterbot.corpus.english.botprofile",
                "chatterbot.corpus.english.literature",
                "chatterbot.corpus.english.movies",
            )
            print("initial training done")

        self.timestamp = time()
        super().__init__(token=TOKEN, prefix='!', initial_channels=[CHANNEL])

    # Detect if a robot server is present in the network
    def _init_server(self):
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        sock.sendto(b'HELLO', ('255.255.255.255', BOT_SERVER_PORT))
        message, address = sock.recvfrom(4096)
        if message == b'ACK':
            self.server_ip = address[0]
            print('server is: %s' % self.server_ip)

    # Send a message to the server (robot)
    def _send_message(self, message):
        s = socket(AF_INET, SOCK_DGRAM)
        s.sendto(message, (self.server_ip, 3636))
        s.close()

    # Say a message
    def _speak(self, message):
        if ROBOT_SPEAKER:
            self._send_message(bytes(message, 'utf-8'))
        else:
            espeak.synth(message)
            while espeak.is_playing():
                pass

    # Trigger robot movement
    def _move(self):
        self._send_message(bytes('MOVE', 'utf-8'))

    # Remove the bot keyword from the message that is sent to pastabot
    def _filter_message_in(self, msg):
        return " ".join([x for x in msg.split(" ") if not BOT_KEYWORD in x])

    # Profanity filter
    def _filter_message_out(self, msg):
        return re.sub('`+', 'PASTA', self.pf.censor(msg)).strip()

    # Print a message to the console to notify that pastabot is logged in
    async def event_ready(self):
        print(f'Logged in as {self.nick}')

    # Main chat message handler
    async def event_message(self, msg):
        if msg.author is None:
            return
        # !pastabot is a special command that is injected to trigger the
        # command below, it can't be used directly, so if it's specified in
        # chat, simply remove it from the message.
        if '!pastabot' in msg.content.lower():
            msg.content.replace('!pastabot', '')
        if PASTACEPTION or msg.author.name != BOT_USER:
            if (BOT_KEYWORD in msg.content.lower()):
                # Respond to message by triggering the !pastabot command
                msg.content = '!pastabot ' + msg.content
        await bot.handle_commands(msg)

    # Suppress command not found exceptions
    async def event_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandNotFound):
            return
        raise error

    # Internal-usage command, used to trigger pastabot response
    @commands.command()
    async def pastabot(self, ctx: commands.Context):
        now = time()
        if (now - self.timestamp) < BOT_COOLDOWN_SEC:
            return
        self.timestamp = now
        msg = ctx.message.content.removeprefix("!pastabot").strip()
        msg = self._filter_message_in(msg)
        if msg != '':
            msg = str(self.bot.get_response(msg))
            msg = self._filter_message_out(msg)
            self._speak(msg)
            self._move()
            await ctx.send(msg)

if __name__ == "__main__":
    bot = Bot()
    bot.run()
