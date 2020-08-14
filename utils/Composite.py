from discord import VoiceChannel, TextChannel, Status
import discord
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import asyncio

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

PLAYER_ONE_START = 169
ROW_HEIGHT = 42

class Composite:
    
    @staticmethod
    async def make(shuffleNum, survivors, infected):
        image = blank.copy()
        draw = ImageDraw.Draw(image)
        Composite.__drawShuffleNumber(draw, shuffleNum)

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
        filename = 'composite.png'
        image.save(filename)
        return filename

    @staticmethod
    def __drawShuffleNumber(draw, shuffleNum):
        text = f"Shuffle {shuffleNum}"
        draw.text((10, 10), text, font=shuffle_font, fill=(81, 81, 81, 255))

    @staticmethod
    async def __drawPlayer(draw, composite, player, character, y):
        profile = await player.getAvatar()

        y += PLAYER_ONE_START
        composite.paste(character, (183, y))
        composite.paste(profile.resize((19,19)), (226, y + 8))
        draw.text(
          (255, y + 11),
          player.getName(),
          font=name_font,
          fill=(81, 81, 81, 255)
        )

