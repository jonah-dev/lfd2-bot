import datetime
import json
import urllib.request
from typing import Dict, Optional

from discord import Embed, Colour, Member, Message
from discord.embeds import EmptyEmbed
from discord.ext import tasks
from discord.ext.commands import command, Cog, Bot, Context

from models.lobby import Lobby


def setup(bot: Bot):
    print("Setting up Lobby cog..")
    bot.add_cog(LobbyCommands(bot))


def teardown(_bot: Bot):
    print("Unloading Lobby cog..")


class LobbyCommands(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.lobbies: Dict[int, Lobby] = {}
        self.janitor: tasks.Loop
        self.janitor.start()

    def cog_unload(self):
        self.janitor.cancel()

    # -------- Helpers --------

    def get_lobby(self, ctx: Context) -> Lobby:
        if ctx.channel.id not in self.lobbies:
            self.lobbies[ctx.channel.id] = Lobby(self.bot, ctx.channel)

        self.lobbies[ctx.channel.id].channel = ctx.channel
        return self.lobbies[ctx.channel.id]

    # -------- Commands --------

    @command()
    async def join(self, ctx: Context):
        """Join the lobby"""
        lobby = self.get_lobby(ctx)
        await lobby.add(ctx.author)

    @command()
    async def add(self, ctx, member: Member):
        """Add another user to the lobby"""
        lobby = self.get_lobby(ctx)
        await lobby.add(member, author=ctx.author)

    @command()
    async def leave(self, ctx: Context):
        """Leave the lobby and prevent others from adding you back"""
        lobby = self.get_lobby(ctx)
        await lobby.remove(ctx.author)

    @command()
    async def remove(self, ctx: Context, member: Member):
        """Remove other users from the lobby"""
        lobby = self.get_lobby(ctx)
        await lobby.remove(member, author=ctx.author)

    @command()
    async def ready(self, ctx: Context):
        """Grab the next available slot in the game"""
        lobby = self.get_lobby(ctx)
        await lobby.ready(ctx.author)

    @command()
    async def flyin(self, ctx):
        """Ready up with enthusiasm"""
        lobby = self.get_lobby(ctx)
        await lobby.ready(ctx.author)

    @command()
    async def unready(self, ctx: Context):
        """Leave your reserved slot"""
        lobby = self.get_lobby(ctx)
        await lobby.unready(ctx.author)

    @command()
    async def lobby(self, ctx: Context):
        """See the current lobby"""
        lobby = self.get_lobby(ctx)
        await lobby.show(temp=False)

    @command()
    async def shuffle(self, ctx: Context):
        """Create teams if possible"""
        lobby = self.get_lobby(ctx)
        await lobby.show_next_shuffle()

    @command()
    async def config(self, ctx: Context, update: Optional[str]):
        """Shows and updates the lobby config"""
        lobby = self.get_lobby(ctx)
        if update:
            # Discord.py parsing breaks on spaces. We want everything.
            update = ctx.message.content.strip("?config ")
            lobby.c.install(update)

        await lobby.show_config()

    @command()
    async def clear(self, ctx: Context):
        """Remove all players from the lobby"""
        if ctx.channel.id in self.lobbies:
            self.lobbies[ctx.channel.id] = Lobby(self.bot, ctx.channel)

        await self.lobbies[ctx.channel.id].show()

    # ------- Events --------

    @Cog.listener()
    async def on_message(self, message: Message):
        if await self.bot.get_prefix(message) != "?":
            return

        ctx = await self.bot.get_context(message)
        if ctx.message.author.bot:
            return

        lobby = self.get_lobby(ctx)

        invoked_with = message.content.partition(" ")[0]
        if invoked_with in lobby.plugin_commands:
            cmd = lobby.plugin_commands[invoked_with]

            # This is a dirty hack to give the cmd access to the lobby
            cmd.cog = lobby

            # All commands take a second 'context' arg including the message
            ctx.args.append(ctx)

            try:
                await cmd.reinvoke(ctx)
            except Exception as err:
                await self.bot.on_command_error(ctx, err)

    # -------- Tasks --------

    # pylint: disable=method-hidden
    @tasks.loop(seconds=60.0)
    async def janitor(self):
        now = datetime.datetime.now().time()
        reset_range_start = datetime.time(13)
        reset_range_end = datetime.time(13, 1)
        if True or reset_range_start <= now <= reset_range_end:
            for index in list(self.lobbies.keys()):
                if len(self.lobbies[index].players) == 0:
                    continue

                channel = self.lobbies[index].channel
                del self.lobbies[index]
                embed = Lobby(self.bot, channel).c.describe()
                embed.color = Colour.orange()
                embed.title = "Lobby has been Cleared"
                embed.set_footer(text=EmptyEmbed)
                await channel.send(embed=embed)
