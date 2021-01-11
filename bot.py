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

import os
from datetime import datetime

from discord.ext.commands.context import Context
from utils.handle import handle

from discord.ext import commands

from models.player import Player


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

        if ctx.command is None:
            return

        await self.invoke(ctx)

    async def on_command_error(self, context: Context, exception):
        await handle(context, exception)

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
        self.load_extension("cogs.misc_commands")

    def run(self, *args, **kwargs):
        """
        This is the final phase of setup. This comes after initialization and
        cog registration. The next step with be authentication of the socket.
        """
        super().run(os.environ["DISCORD_TOKEN"])

    @staticmethod
    def is_admin(author):
        """
        For reliability and safety reasons, there are some admin controls
        loosely gated by this check. These are the Discord IDs of primary
        admin users.
        """
        return author.id in [147788154831634434, 236938533179228162]


print("Booting up the bot")
bot = LFD2Bot()
print(f"Bot Initialized at: {datetime.now()}")
bot.load_cogs()
bot.run()
