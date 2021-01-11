import os
from typing import List

from discord.ext.commands import command, Cog, Bot, Context


def setup(bot: Bot):
    print("Setting up admin cog..")
    admins = None
    if os.environ.get("DISCORD_ADMINS") is not None:
        admins = os.environ.get("DISCORD_ADMINS").split(" ")
        admins = [int(i) for i in admins]
        print(f"Registered Admins: {admins}")

    bot.add_cog(AdminCommands(bot, admins))


def teardown(_bot: Bot):
    print("Unloading admin cog..")


class AdminCommands(Cog):
    def __init__(self, bot: Bot, admins: List[int]):
        self.bot: Bot = bot
        self.admins: List[int] = admins

    def cog_unload(self):
        self.janitor.cancel()

    @command(hidden=True)
    async def disconnect(self, ctx: Context):
        if not self.is_admin(ctx.author):
            return

        author = f"{ctx.author.name}#{ctx.author.discriminator}"
        print(f"Command: disconnect (author: {author})")
        await self.bot.close()

    # -------- Helpers --------

    def is_admin(self, author):
        return self.admins is not None and author.id in self.admins
