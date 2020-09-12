from typing import Tuple
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import asyncio

from models.Lobby import Lobby
from models.Player import Player

name_font = ImageFont.truetype("assets/AmazMegaGrungeOne.ttf", 16)
shuffle_font = ImageFont.truetype("assets/AmazMegaGrungeOne.ttf", 36)

blank = Image.open("assets/lobby.png")
infected_character = Image.open('assets/infected_small.png')
survivor_characters = [
  Image.open('assets/coach_small.png'),
  Image.open('assets/ellis_small.jpeg'),
  Image.open('assets/nick_small.png'),
  Image.open('assets/rochelle_small.png'),
]

is_ready = Image.open('assets/ready.png')
not_ready = Image.open('assets/not_ready.png')
voice_on = Image.open('assets/voice_on.png')
voice_off = Image.open('assets/voice_off.png')

PLAYER_ONE_START = 169
ROW_HEIGHT = 42

class Composite:
    
    @staticmethod
    async def make(lobby: Lobby, survivors: Tuple[Player, ...], infected: Tuple[Player, ...]) -> str:
        image = blank.copy()
        draw = ImageDraw.Draw(image)
        Composite.__drawShuffleNumber(draw, lobby.shuffleNum)

        ops = []
        for index, player in enumerate(survivors):
          character = survivor_characters[index]
          y = index * ROW_HEIGHT
          ops.append(Composite.__drawPlayer(draw, image, player, character, y))

        character = infected_character
        for index, player in enumerate(infected):
          y = (index + len(survivors)) * ROW_HEIGHT
          ops.append(Composite.__drawPlayer(draw, image, player, character, y))

        await asyncio.wait(ops)
        filename = f"assets/temp/composite-{lobby.channel.id}.png"
        image.save(filename)
        return filename

    @staticmethod
    def __drawShuffleNumber(draw: ImageDraw.Draw, shuffleNum: int) -> None:
        text = f"Shuffle {shuffleNum}"
        draw.text((10, 10), text, font=shuffle_font, fill=(81, 81, 81, 255))

    @staticmethod
    async def __drawPlayer(draw: ImageDraw.Draw, composite: Image, player: Player, character: Image, y: int) -> None:
        profile = await player.getAvatar()
        ready = is_ready if player.isReady() else not_ready
        voice = voice_on if player.isInVoice() else voice_off

        y += PLAYER_ONE_START
        composite.paste(ready, (132, y + 11), ready)
        composite.paste(voice, (155, y + 5), voice)
        composite.paste(character, (183, y))
        composite.paste(profile.resize((19,19)), (226, y + 8))
        draw.text(
          (255, y + 11),
          player.getName(),
          font=name_font,
          fill=(81, 81, 81, 255)
        )

