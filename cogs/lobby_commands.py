import datetime
import json
import urllib.request
from typing import Dict

from discord import Embed, Colour, Member
from discord.ext import tasks
from discord.ext.commands import command, Cog, Bot, Context

from models.lobby import Lobby
from utils.usage_exception import UsageException
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

    async def get_lobby_then(self, ctx: Context, do_command) -> None:
        if ctx.channel.id in self.lobbies:
            self.lobbies[ctx.channel.id].channel = ctx.channel
            return await do_command(self.lobbies[ctx.channel.id])

        await ctx.send("You haven't started a lobby. Use `?start` to open a new lobby.")

    # -------- Commands --------

    @command()
    async def help(self, ctx: Context):
        embed = Embed(colour=Colour.orange())
        embed.set_author(name="Help")
        embed.add_field(name="?join", value="Joins the lobby", inline=False)
        embed.add_field(name="?leave", value="Leaves the lobby", inline=False)
        embed.add_field(name="?lobby", value="Views the lobby", inline=False)
        embed.add_field(name="?ready", value="Readies your user", inline=False)
        embed.add_field(name="?unready", value="Unreadies your user", inline=False)
        embed.add_field(
            name="?shuffle",
            value="Creates a randomly shuffled set of teams with the given lobby.",
            inline=False,
        )
        embed.add_field(
            name="?remove [player]", value="Removes player by tag", inline=False
        )
        embed.add_field(name="?reset", value="Resets the lobby", inline=False)
        await ctx.send(embed=embed)

    @command()
    async def start(self, ctx: Context):
        if ctx.channel.id in self.lobbies:
            raise UsageException(
                ctx.channel,
                "The lobby has already been started. You can restart the lobby with `?reset`.",
            )

        self.lobbies[ctx.channel.id] = Lobby(self.bot, ctx.channel)
        await ctx.send("The lobby has been started!")

    @command()
    async def join(self, ctx: Context):
        await self.get_lobby_then(ctx, lambda lobby: lobby.add(ctx.author))

    @command()
    async def add(self, ctx, member: Member):
        await self.get_lobby_then(ctx, lambda lobby: lobby.add(member, author=ctx.author))
    @command()
    async def leave(self, ctx: Context):
        await self.get_lobby_then(ctx, lambda lobby: lobby.remove(ctx.author))

    @command()
    async def remove(self, ctx: Context, member: Member):
        await self.get_lobby_then(ctx, lambda lobby: lobby.remove(member))

    @command()
    async def ready(self, ctx: Context):
        await self.get_lobby_then(ctx, lambda lobby: lobby.ready(ctx.author))

    @command()
    async def unready(self, ctx: Context):
        await self.get_lobby_then(ctx, lambda lobby: lobby.unready(ctx.author))

    @command()
    async def flyin(self, ctx):
        await self.get_lobby_then(ctx, lambda lobby: lobby.flyin(ctx.author))

    @command()
    async def numbers(self, ctx: Context):
        await self.get_lobby_then(ctx, lambda lobby: lobby.show_numbers())

    @command()
    async def lobby(self, ctx: Context):
        await self.get_lobby_then(ctx, lambda lobby: lobby.show_lobby())

    @command()
    async def shuffle(self, ctx: Context):
        await self.get_lobby_then(ctx, lambda lobby: lobby.show_next_match(get_shuffler))
    
    @command()
    async def ranked(self, ctx: Context):
        await self.get_lobby_then(ctx, lambda lobby: lobby.show_next_match(get_ranker(ctx.channel)))

    @command()
    async def reset(self, ctx: Context):
        created = "reset" if ctx.channel.id in self.lobbies else "started"
        self.lobbies[ctx.channel.id] = Lobby(self.bot, ctx.channel)
        await ctx.send(f"The lobby has been {created}!")

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
                embed.set_author(name=f"Daily Update - {str(datetime.date.today())}")
                embed.add_field(
                    name="Lobby has been cleared!", value=daily_fact, inline=False
                )
                await channel.send(embed=embed)

    @staticmethod
    def get_todays_useless_fact():
        req = urllib.request.urlopen(
            "https://uselessfacts.jsph.pl/today.json?language=en"
        )
        return json.loads(req.read())["text"]
