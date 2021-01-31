import random
import pytz
from datetime import datetime

from discord.ext.commands import command, Cog, Bot, Context


def setup(bot: Bot):
    print("Setting up misc cog..")
    bot.add_cog(MiscCommands(bot))


def teardown(_bot: Bot):
    print("Unloading misc cog..")


class MiscCommands(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    def cog_unload(self):
        self.janitor.cancel()

    @command(hidden=True)
    async def lag(self, ctx: Context):
        # TODO(jonah-dev) Explain yourself
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
            author = ctx.author.display_name
            await ctx.send(f"Current lag for {author} is: {lag}ms")

    @command(hidden=True)
    async def ped(self, ctx: Context):
        await ctx.send(f"Current lag for {ctx.author.display_name} is: {0}ms")

    @command(hidden=True)
    async def time(self, ctx: Context):
        """Displays the official discord time"""
        tz = pytz.timezone('US/Pacific')
        msg = "The official discord time is: " + datetime.now(tz).strftime("%I:%M %p")
        await ctx.send(msg)
