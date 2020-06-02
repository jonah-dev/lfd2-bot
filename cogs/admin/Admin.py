from discord.ext import commands
import discord



class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    #TODO: Allow this to be pulled from the config file
    async def is_admin(self, ctx):
        return ctx.author.id in [147788154831634434]

    # Mostly a test, we can remove this later
    @commands.command()
    @commands.check(is_admin)
    async def adminCheck(self, ctx):
        await ctx.send("You are an admin")

    
# Cog Lifecycle Methods
def setup(bot):
    print('Setting up Admin cog..')
    bot.add_cog(Admin(bot))

def teardown(bot):
    print('Unloading Admin cog..')

