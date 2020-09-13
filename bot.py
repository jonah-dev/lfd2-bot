"""
Welcome to the L4D2 Discord Lobby bot. This project
leverages discord.py heavily. Consider reading their
documentation at https://discordpy.readthedocs.io

Follow these steps to create a bot-user to serve as:
https://discordpy.readthedocs.io/en/latest/discord.html

In order for the bot to run, you must set a DISCORD_TOKEN
environment variable. This is found in the 'bot' section
of Discord's developer studio.
"""

import random
import os
import logging
import traceback
from datetime import datetime

from discord.ext import commands

from models.player import Player

from utils.usage_exception import UsageException

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("LFD2Bot")


class LFD2Bot(commands.Bot):
    """
    This is the entrypoint of the lobby bot. You'll find...
     - Integration point for discord.py
     - Several top-level commands
     - Managing command extensions (cogs)
     - Error handling and reporting
     - Retaining global in-memory state.
    """

    # Init and setup
    def __init__(self):
        super().__init__(
            command_prefix="?",
            description="Organize your LFD2 Games with ease",
            pm_help=None,
            help_attrs=dict(hidden=False),
            fetch_offline_members=False,
        )

    async def on_message(self, message):
        if message.author.bot:
            return

        await self.process_commands(message)

    async def process_commands(self, message):
        ctx = await self.get_context(message)

        if message.content == "disconnect" and self.is_admin(ctx.author):
            print("disconnecting")
            await self.close()

        if message.content == "?commands":
            await ctx.send(
                """```\n
                ?start - Initializes the lobby \n
                ?join - Joins the lobby \n
                ?leave - Leaves the lobby \n
                ?lobby - View the lobby \n
                ?order66 - Issues a ping that marks the beginning of the game \n
                ?lag - Calculates your current lag \n
                ?ped - FOOTBALL SZN \n
                ?ready - Ready up! \n
                ?unready - Not R! \n
                ```"""
            )

        # Need to move this into a "funny commands" cog
        if message.content == "?lag":
            now = datetime.now()
            lag_range = dict()
            lag_range[19, 20] = 20
            lag_range[20, 21] = 40
            lag_range[21, 22] = 60
            lag_range[22, 23] = 80
            lag_range[23, 24] = 100
            lag_range[0, 1] = 120
            lag_range[1, 2] = 140
            lag_range[2, 3] = 200
            lag_range[4, 5] = 220
            lag_range[5, 6] = 320
            lag_range[6, 7] = 420
            current_time = int(now.strftime("%H").strip("0"))
            lag = None
            for key, value in lag_range.items():
                low, high = key
                if int(low) <= current_time <= int(high):
                    lag = value * (1 + (random.randint(1, 5) * 0.1))
            if lag is None:
                await ctx.send("No lag at this current time")
            else:
                author = Player(ctx.author).getName()
                await ctx.send(f"Current lag for {author} is: {lag}ms")
            return

        # Need to move this into a "funny commands" cog
        if message.content == "?ped":
            await ctx.send(f"Current lag for {Player(ctx.author).getName()} is: {0}ms")

        if ctx.command is None:
            return

        await self.invoke(ctx)

    async def on_command_error(self, context, exception):
        if isinstance(exception, UsageException):
            await exception.notice()
            return

        await context.send("There was an error during your command :worried:")
        trace = traceback.TracebackException.from_exception(exception.__cause__)
        pretty_trace = "".join(trace.format())
        logger.error('Command: "%s"\n%s', context.message.content, pretty_trace)

    async def on_ready(self):
        """Lifecycle Event: Bot is initialized and authenticated."""
        print("Logged on as", self.user)

    async def close(self):
        """Lifecycle Event: Bot will shut down soon."""
        await super().close()

    def load_cogs(self):
        """
        Logically grouped commands can be moved to individual 'cogs'. We need
        to then register them with discord.py. This is the full collection.
        """
        self.load_extension("cogs.lobby_commands")

    def run(self, *args, **kwargs):
        """
        This is the final phase of setup. This comes after initialization and
        cog registration. The next step with be authentication of the socket.
        """
        super().run(os.environ["DISCORD_TOKEN"])

    @staticmethod
    def is_admin(author):
        """
        For reliability and safety reasons, there are some admin controls loosely
        gated by this check. These are the Discord IDs of primary admin users.
        """
        return author.id in [147788154831634434, 236938533179228162]


print("Booting up the bot")
bot = LFD2Bot()
bot.remove_command("help")
print(f"Bot Initialized at: {datetime.now()}")
bot.load_cogs()
bot.run()
