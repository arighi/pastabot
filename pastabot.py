#!/usr/bin/env python
#
# Twitch chat bot that interacts with OpenAI.

import os
import re
import asyncio
from twitchio.ext import commands
from time import time

# Twitch login token and OpenAI key are defined in cred.py
from cred import TOKEN, API_KEY

import openai
openai.api_key = API_KEY

import logging
logger = logging.getLogger()

### Bot settings ###

# Twitch identity / channel
CHANNEL="the_pastabot"
BOT_USER="the_pastabot"
BOT_KEYWORD = 'pastabot'

# Cooldown between a response and another
BOT_COOLDOWN_SEC = 5

# Bot responses can trigger other responses if keyword is present
#
# WARNING: this can trigger loops in the Twitch chat if enabled
# (only use for testing)!
PASTACEPTION = False

# Main chat bot class
class Bot(commands.Bot):
    def __init__(self):
        # Initialize communication with robot
        self.timestamp = time()
        self.pasta_enabled = True
        super().__init__(token=TOKEN, prefix='!', initial_channels=[CHANNEL])

    # Remove the bot keyword from the message that is sent to pastabot
    def _filter_message_in(self, msg):
        return " ".join([x for x in msg.split(" ") if not BOT_KEYWORD in x.lower()])

    # Print a message to the console to notify that pastabot is logged in
    async def event_ready(self):
        logger.critical(f'Logged in as {self.nick}')

    # Check if the user that requested the command is a sub
    async def _sub_check(self, ctx):
        if ctx.author.is_mod or ctx.author.is_subscriber:
            return True
        await ctx.send(f"@{ctx.author.name} this command is reserved to subscribers")
        return False

    # Check if the user that requested the command is a mod
    async def _mod_check(self, ctx):
        if ctx.author.is_mod:
            return True
        await ctx.send(f"@{ctx.author.name} this command is reserved to mods")
        return False

    # Suppress command not found exceptions
    async def event_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandNotFound):
            return
        raise error

    # Main chat message handler
    async def event_message(self, msg):
        if msg.author is None:
            return
        # !pastabot is a special command that is injected to trigger the
        # command below, it can't be used directly, so if it's specified in
        # chat, simply remove it from the message.
        if '!pastabot' in msg.content.lower():
            msg.content.replace('!pastabot', '')
        if PASTACEPTION or \
           (msg.author.name != BOT_USER and msg.author.name != 'streamelements'):
            if self.pasta_enabled and (BOT_KEYWORD in msg.content.lower()):
                # Respond to message by triggering the !pastabot command
                msg.content = '!pastabot ' + msg.content
        await bot.handle_commands(msg)

    # Get response from OpenAI
    def _openai_response(self, msg):
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=msg,
            max_tokens=1000,
            n=1,
            stop=None,
            temperature=0.9,
        )
        text = response["choices"][0]["text"]
        output = ' '.join([line for line in text.split('\n') if line.strip() != ''])
        output = output.lstrip(' ?!')
        return re.sub(r'^[^\x00-\x7F]+', '', output)

    # Split long response into multiple smaller responses
    @staticmethod
    def _split_response(string, length):
        words = string.split()
        result = []
        current = []
        for word in words:
            if len(" ".join(current + [word])) <= length:
                current.append(word)
            else:
                result.append(" ".join(current))
                current = [word]
        result.append(" ".join(current))
        return result

    # Internal-usage command, used to trigger pastabot response
    @commands.command()
    async def pastabot(self, ctx: commands.Context):
        now = time()
        if (now - self.timestamp) < BOT_COOLDOWN_SEC:
            return
        self.timestamp = now
        orig_msg = ctx.message.content.removeprefix("!pastabot").strip()
        msg = self._filter_message_in(orig_msg)
        if msg == '':
            logger.critical('warning: invalid input message')
            return
        logger.critical(f'input: {msg}')
        msg = self._openai_response(msg)
        # Drop empty responses or responses that are too long
        logger.critical(f'output: {msg}')
        if len(msg) == 0 or len(msg) > 1000:
            msg = 'I have nothing to say'
        for line in self._split_response(msg, 500):
            logger.critical(f'chat: {msg}')
            await ctx.send(line)

    ### Mod-only commands ###

    @commands.command()
    async def bot_on(self, ctx: commands.Context):
        if await self._mod_check(ctx):
            self.pasta_enabled = True
            logger.critical(f'{BOT_KEYWORD} is on')
            await ctx.send(f'{BOT_KEYWORD} activated')

    @commands.command()
    async def bot_off(self, ctx: commands.Context):
        if await self._mod_check(ctx):
            self.pasta_enabled = False
            logger.critical(f'{BOT_KEYWORD} is off')
            await ctx.send(f"{BOT_KEYWORD} is now sleeping, zzz...")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s >> %(message)s',
                        datefmt="%Y-%m-%d %H:%M:%S")
    bot = Bot()
    bot.run()
