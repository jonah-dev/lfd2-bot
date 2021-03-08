import asyncio
import atexit
from plugins.SuperCashBrosLeftForDead.game_data import (
    ACTIVE_PLAYER_DATE_THRESHOLD,
    ACTIVE_PLAYER_GAMES_THRESHOLD,
)
from plugins.SuperCashBrosLeftForDead.ranker import (
    AVERAGE_SCORE,
    GAME_WEIGHT_HALFLIFE_DAYS,
)
from typing import List

from PIL import Image, ImageDraw, ImageFont

from models.player import Player

name_font = ImageFont.truetype("assets/AmazMegaGrungeOne.ttf", 16)
shuffle_font = ImageFont.truetype("assets/AmazMegaGrungeOne.ttf", 36)
tip_font = ImageFont.truetype("assets/AmazMegaGrungeOne.ttf", 14)

blank = Image.open("assets/lobby.png")
infected_character = Image.open("assets/infected_small.png")
survivor_characters = [
    Image.open("assets/coach_small.png"),
    Image.open("assets/ellis_small.jpeg"),
    Image.open("assets/nick_small.png"),
    Image.open("assets/rochelle_small.png"),
]

is_ready = Image.open("assets/ready.png")
not_ready = Image.open("assets/not_ready.png")
voice_on = Image.open("assets/voice_on.png")
voice_off = Image.open("assets/voice_off.png")

PLAYER_ONE_START = 169
ROW_HEIGHT = 42


async def draw_composite(
    game_num: int,
    survivors: List[Player],
    infected: List[Player],
    channel_id: int,
) -> str:
    image = blank.copy()
    draw = ImageDraw.Draw(image)
    draw_game_number(draw, game_num)
    draw_ranking_tip(draw)

    ops = []
    for index, player in enumerate(survivors):
        character = survivor_characters[index]
        y_offset = index * ROW_HEIGHT
        ops.append(draw_player(draw, image, player, character, y_offset))

    character = infected_character
    for index, player in enumerate(infected):
        y_offset = (index + len(survivors)) * ROW_HEIGHT
        ops.append(draw_player(draw, image, player, character, y_offset))

    if len(ops) > 0:
        await asyncio.wait(ops)
    filename = f"assets/temp/composite-{channel_id}.png"
    image.save(filename)
    return filename


def draw_game_number(draw: ImageDraw.Draw, shuffle_num: int) -> None:
    text = f"Match {shuffle_num + 1}"
    draw.text((10, 10), text, font=shuffle_font, fill=(81, 81, 81, 255))


def draw_ranking_tip(draw: ImageDraw.Draw) -> None:
    games = ACTIVE_PLAYER_GAMES_THRESHOLD
    days = ACTIVE_PLAYER_DATE_THRESHOLD.days
    line = f"Active players have played {games} games in the past {days} days"
    draw.text((10, 60), line, font=tip_font, fill=(81, 81, 81, 255))

    decay = GAME_WEIGHT_HALFLIFE_DAYS
    line = f"Player ranks consider all active players ({decay} day decay)"
    draw.text((10, 76), line, font=tip_font, fill=(81, 81, 81, 255))

    default_rank = AVERAGE_SCORE
    line = f"Inactive players are given the default rank ({default_rank})"
    draw.text((10, 94), line, font=tip_font, fill=(81, 81, 81, 255))


async def draw_player(
    draw: ImageDraw.Draw,
    composite: Image,
    player: Player,
    character: Image,
    y_offset: int,
) -> None:
    profile = await player.get_avatar()
    ready = is_ready if player.is_ready() else not_ready
    voice = voice_on if player.is_in_voice() else voice_off

    y_offset += PLAYER_ONE_START
    composite.paste(ready, (132, y_offset + 11), ready)
    composite.paste(voice, (155, y_offset + 5), voice)
    composite.paste(character, (183, y_offset))
    composite.paste(profile.resize((19, 19)), (226, y_offset + 8))
    draw.text(
        (255, y_offset + 11),
        player.get_name(),
        font=name_font,
        fill=(81, 81, 81, 255),
    )


@atexit.register
def close_files():
    blank.close()
    infected_character.close()
    is_ready.close()
    not_ready.close()
    voice_on.close()
    voice_off.close()
    for i in survivor_characters:
        i.close()
