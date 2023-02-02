### Register all your custom plugins here ###

from twitchio.ext import commands

# Base plugin class
class BotPlugin(object):
    def __init__(self, bot):
        self.bot = bot

    def register_command(self, name, callback):
        @self.bot.command(name=name)
        async def dynamic_command(ctx: commands.Context):
            await callback(ctx)

# Basic hello world plugin
class HelloWorldPlugin(BotPlugin):
    def __init__(self, bot):
        super().__init__(bot)
        super().register_command("hello", self.hello)

    async def hello(self, ctx: commands.Context):
        await ctx.send("hello world")

# Main plugin register interface
class Plugins:
    def __init__(self, bot):
        HelloWorldPlugin(bot)
