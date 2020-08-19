from typing import Optional
import discord
from PIL import Image
import io

class Player():
    def __init__(self, member: discord.Member):
        self.member: discord.Member = member
        self.ready: bool = False
        self.__cachedAvatar: Optional[Image] = None

    def isReady(self) -> bool:
        return self.ready

    def getName(self) -> str:
        if self.member.display_name == None:
          return ''
        return self.member.display_name
    
    def getMention(self) -> str:
        return self.member.mention

    def setReady(self) -> None:
        self.ready = True

    def setUnready(self) -> None:
        self.ready = False

    async def getAvatar(self) -> Image:
        if (self.__cachedAvatar is not None):
          return self.__cachedAvatar

        url = self.member.avatar_url_as(static_format="png", size=1024)
        data = await url.read()
        image = Image.open(io.BytesIO(data))
        self.__cachedAvatar = image
        return image

    def isInVoice(self) -> bool:
        state = self.member.voice
        return state is not None and state.channel is not None

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Player) and self.member.id == other.member.id

    def __ne__(self, other: object) -> bool:
        return isinstance(other, Player) and self.member.id != other.member.id

    def __gt__(self, other: object) -> bool:
        return isinstance(other, Player) and self.member.id > other.member.id
    
    def __ge__(self, other: object) -> bool:
        return isinstance(other, Player) and self.member.id >= other.member.id
    
    def __le__(self, other: object) -> bool:
        return isinstance(other, Player) and self.member.id <= other.member.id
    
    def __lt__(self, other: object) -> bool:
        return isinstance(other, Player) and self.member.id < other.member.id
    
    def __hash__(self) -> int:
        return self.member.id