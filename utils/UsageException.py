from discord import TextChannel

class UsageException(Exception):

    def __init__(self, ctx: TextChannel, message: str):
        self.ctx = ctx
        self.message = message
        super().__init__(self.message)
    
    async def notice(self):
        await self.ctx.send(self.message)