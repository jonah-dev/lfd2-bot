
import discord
from pprint import pprint
from PIL import Image
import io

class Player():
    def __init__(self, member: discord.Member):
        self.member = member
        self.ready = False

    def isReady(self):
        return self.ready

    def getName(self):
        if self.member.display_name == None:
          return ''
        return self.member.display_name
    
    def getMention(self):
        return self.member.mention

    def setType(self, player_type: str):
        self.player_type = player_type

    def setReady(self):
        self.ready = True

    def setUnready(self):
        self.ready = False

    async def getAvatar(self):
        #TODO Cache these byte objects in database
        byteObject = await self.member.avatar_url_as(static_format="png", size=1024).read()
        return Image.open(io.BytesIO(byteObject))

    def __eq__(self, other):
        if (isinstance(other, Player)):
            return self.member.id == other.member.id
        return False

    def __ne__(self, other):
        return self.member.id != other.member.id

    def __gt__(self, other):
        return self.member.id > other.member.id
    
    def __ge__(self, other):
        return self.member.id >= other.member.id
    
    def __le__(self, other):
        return self.member.id <= other.member.id
    
    def __lt__(self, other):
        return self.member.id < other.member.id
    
    def __hash__(self):
        return self.member.id