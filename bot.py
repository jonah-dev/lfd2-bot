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
from discord.ext import commands
from discord import Intents
from utils.handle import handle


intents = Intents.default()
intents.members = True

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
            fetch_offline_members=True,
            intents=intents,
        )
    
    async def on_message(self, message):
        if message.author.bot:
            return

        ctx = await self.get_context(message)
        if ctx.command is None:
            return # Ignore unknown messages
        
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
        self.load_extension("cogs.admin_commands")

    def run(self, *args, **kwargs):
        """
        This is the final phase of setup. This comes after initialization and
        cog registration. The next step with be authentication of the socket.
        """
        super().run(os.environ["DISCORD_TOKEN"])


print("Booting up the bot")
bot = LFD2Bot()
print(f"Bot Initialized at: {datetime.now()}")
bot.load_cogs()
bot.run()
