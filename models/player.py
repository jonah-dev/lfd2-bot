import io
from typing import Optional

import discord
from PIL import Image


class Player:
    def __init__(self, member: discord.Member):
        self.member: discord.Member = member
        self.ready: bool = False
        self.__cached_avatar: Optional[Image] = None

    def is_ready(self) -> bool:
        return self.ready

    def get_name(self) -> str:
        return self.member.display_name

    def get_mention(self) -> str:
        return self.member.mention

    def set_ready(self) -> None:
        self.ready = True

    def set_unready(self) -> None:
        self.ready = False

    async def get_avatar(self) -> Image:
        if self.__cached_avatar is not None:
            return self.__cached_avatar

        url = self.member.avatar_url_as(static_format="png", size=1024)
        data = await url.read()
        image = Image.open(io.BytesIO(data))
        self.__cached_avatar = image
        return image

    def is_in_voice(self) -> bool:
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
