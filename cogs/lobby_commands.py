import datetime
import json
import urllib.request
from typing import Dict
from utils.option_switch import option_switch

from discord import Embed, Colour, Member
from discord.ext import tasks
from discord.ext.commands import command, Cog, Bot, Context

from models.lobby import Lobby
from matchmaking.linear_regression_ranker import get_ranker
from matchmaking.random_shuffler import get_shuffler


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
    async def help(self, ctx: Context):
        embed = Embed(colour=Colour.orange())
        embed.set_author(name="Help")
        embed.add_field(name="?join", value="Joins the lobby", inline=False)
        embed.add_field(name="?leave", value="Leaves the lobby", inline=False)
        embed.add_field(name="?lobby", value="Views the lobby", inline=False)
        embed.add_field(name="?ready", value="Readies your user", inline=False)
        embed.add_field(
            name="?unready", value="Unreadies your user", inline=False
        )
        embed.add_field(
            name="?shuffle",
            value="Provides randomly decided teams.",
            inline=False,
        )
        embed.add_field(
            name="?remove [player]",
            value="Removes player by tag",
            inline=False,
        )
        embed.add_field(name="?reset", value="Resets the lobby", inline=False)
        await ctx.send(embed=embed)

    @command()
    async def join(self, ctx: Context):
        lobby = self.get_lobby(ctx)
        await lobby.add(ctx.author)

    @command()
    async def add(self, ctx, member: Member):
        lobby = self.get_lobby(ctx)
        await lobby.add(member, author=ctx.author)

    @command()
    async def leave(self, ctx: Context):
        lobby = self.get_lobby(ctx)
        await lobby.remove(ctx.author)

    @command()
    async def remove(self, ctx: Context, member: Member):
        lobby = self.get_lobby(ctx)
        await lobby.remove(member, author=ctx.author)

    @command()
    async def ready(self, ctx: Context):
        lobby = self.get_lobby(ctx)
        await lobby.ready(ctx.author)

    @command()
    async def flyin(self, ctx):
        lobby = self.get_lobby(ctx)
        await lobby.ready(ctx.author)

    @command()
    async def unready(self, ctx: Context):
        lobby = self.get_lobby(ctx)
        await lobby.unready(ctx.author)

    @command()
    async def lobby(self, ctx: Context):
        lobby = self.get_lobby(ctx)
        await lobby.show(temp=False)

    @command()
    async def shuffle(self, ctx: Context):
        lobby = self.get_lobby(ctx)
        await lobby.show_next_match(get_shuffler())

    @command()
    async def ranked(self, ctx: Context):
        lobby = self.get_lobby(ctx)
        await lobby.show_next_match(get_ranker(ctx.channel)),

    @command()
    async def leaderboard(self, ctx: Context, option: str = None):
        then = option_switch(
            ctx.channel,
            option,
            {
                "lobby": lambda l: l.show_ranking(filter_lobby=True),
                None: lambda l: l.show_ranking(filter_lobby=False),
            },
        )

        lobby = self.get_lobby(ctx)
        await then(lobby)

    @command()
    async def clear(self, ctx: Context):
        if ctx.channel.id in self.lobbies:
            self.lobbies[ctx.channel.id] = Lobby(self.bot, ctx.channel)

        await self.lobbies[ctx.channel.id].show()

    # -------- Tasks --------

    # pylint: disable=method-hidden
    @tasks.loop(seconds=60.0)
    async def janitor(self):
        now = datetime.datetime.now().time()
        reset_range_start = datetime.time(13)
        reset_range_end = datetime.time(13, 1)
        if reset_range_start <= now <= reset_range_end:
            daily_fact = self.get_todays_useless_fact()
            for index in self.lobbies:
                if len(self.lobbies[index].players) == 0:
                    continue

                channel = self.lobbies[index].channel
                self.lobbies[index] = Lobby(self.bot, channel)
                embed = Embed(colour=Colour.orange())
                embed.set_author(
                    name=f"Daily Update - {str(datetime.date.today())}"
                )
                embed.add_field(
                    name="Lobby has been cleared!",
                    value=daily_fact,
                    inline=False,
                )
                await channel.send(embed=embed)

    @staticmethod
    def get_todays_useless_fact():
        req = urllib.request.urlopen(
            "https://uselessfacts.jsph.pl/today.json?language=en"
        )
        return json.loads(req.read())["text"]
