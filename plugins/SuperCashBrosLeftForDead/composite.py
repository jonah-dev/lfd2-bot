import asyncio
import atexit
import plugins.SuperCashBrosLeftForDead.ranking_config as rc
from typing import Callable, List

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

diamond = Image.open("assets/diamond.png")
gold = Image.open("assets/gold.png")
silver = Image.open("assets/silver.png")
bronze = Image.open("assets/bronze.png")

PLAYER_ONE_START = 169
ROW_HEIGHT = 42


async def draw_composite(
    game_num: int,
    survivors: List[Player],
    infected: List[Player],
    channel_id: int,
    get_rank: Callable[[int], int],
) -> str:
    image = blank.copy()
    draw = ImageDraw.Draw(image)
    draw_game_number(draw, game_num)
    rc.USE_ROLLING_SEASON and draw_season_info(draw)

    ops = []
    for index, player in enumerate(survivors):
        character = survivor_characters[index]
        rank = get_rank_image(get_rank(player.member.id))
        y_offset = index * ROW_HEIGHT
        ops.append(draw_player(draw, image, player, character, rank, y_offset))

    character = infected_character
    for index, player in enumerate(infected):
        y_offset = (index + len(survivors)) * ROW_HEIGHT
        rank = get_rank_image(get_rank(player.member.id))
        ops.append(draw_player(draw, image, player, character, rank, y_offset))

    if len(ops) > 0:
        await asyncio.wait(ops)
    filename = f"assets/temp/composite-{channel_id}.png"
    image.save(filename)
    return filename


def draw_game_number(draw: ImageDraw.Draw, shuffle_num: int) -> None:
    text = f"Match {shuffle_num + 1}"
    draw.text((10, 10), text, font=shuffle_font, fill=(81, 81, 81, 255))


def draw_season_info(draw: ImageDraw.Draw) -> None:
    line = f"Ranking considers all games in the past {rc.LENGTH_DAYS} days"
    draw.text((14, 60), line, font=tip_font, fill=(81, 81, 81, 255))

    line = f"You must play {rc.PLACEMENT_GAMES} in this time to be ranked"
    draw.text((10, 76), line, font=tip_font, fill=(81, 81, 81, 255))

    line = "New and unranked players will be ranked using all available data"
    draw.text((10, 94), line, font=tip_font, fill=(81, 81, 81, 255))


async def draw_player(
    draw: ImageDraw.Draw,
    composite: Image,
    player: Player,
    character: Image,
    rank: Image,
    y_offset: int,
) -> None:

    ready = is_ready if player.is_ready() else not_ready
    voice = voice_on if player.is_in_voice() else voice_off

    y_offset += PLAYER_ONE_START
    composite.paste(rank, (88, y_offset), rank)
    composite.paste(ready, (132, y_offset + 11), ready)
    composite.paste(voice, (155, y_offset + 5), voice)
    composite.paste(character, (183, y_offset))

    try:
        profile = await player.get_avatar()
        composite.paste(profile.resize((19, 19)), (226, y_offset + 8))
    except Exception:
        pass

    draw.text(
        (255, y_offset + 11),
        player.get_name(),
        font=name_font,
        fill=(81, 81, 81, 255),
    )


def get_rank_image(rank):
    if rank is None:
        return None
    elif rank > 3800:
        return diamond
    elif rank > 2800:
        return gold
    elif rank > 1800:
        return silver
    else:
        return bronze


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
