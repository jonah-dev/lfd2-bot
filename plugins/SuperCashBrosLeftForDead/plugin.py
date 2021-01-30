from discord import Colour, Embed, File
from discord.ext.commands.context import Context
from discord.ext.commands.core import command

from models.lobby import Lobby
from models.player import Player
from .ranker import get_player_ranks, rank
from .composite import draw_composite
from .game_data import GameData
from utils.directive import directive, parse_multi
from utils.usage_exception import UsageException


@directive
def SuperCashBrosLeftForDead(config, props: str):
    config.vMax = 8
    config.vMin = 8
    config.vOverflow = True
    config.vTeams = [4, 4]

    config.pLeft4Dead = {}

    if not props:
        return

    props = parse_multi(props)
    if type(props) is not dict:
        config.issue("You must provide named properties.")
        return

    if "history" in props:
        history = props["history"]
        if type(history) is not str:
            config.issue("'history' must be a google sheet. (see the docs)'")
        else:
            config.pLeft4Dead["history"] = history
            config.installCommand(ranked)
            config.installCommand(leaderboard)


@command()
async def ranked(lobby: "Lobby", ctx: Context):
    """Create fair teams based on player history"""
    if not lobby.is_ready():
        raise UsageException.not_enough_for_match(lobby.channel)

    if __name__ not in lobby._cache:
        id = lobby.c.pLeft4Dead["history"]
        matches = lobby.get_matches()
        await rank(matches, id, lobby.channel)
        lobby._cache[__name__] = iter(enumerate(matches))

    next_match = next(lobby._cache[__name__], None)
    if next_match is None:
        raise UsageException.seen_all_matches(lobby.channel)

    i, teams = next_match
    teams = list(teams)
    team1, team2 = list(teams)[0], list(teams[1])
    composite = await draw_composite(i, team1, team2, lobby.channel.id)
    await ctx.send(file=File(composite))


@command()
async def leaderboard(lobby, ctx: Context, option: str = None):
    """See player ranks"""
    filter_lobby = option == "lobby"
    id = lobby.c.pLeft4Dead["history"]
    data = await GameData.fetch(id, lobby.channel)
    scores = get_player_ranks(data)
    scores = scores.items()
    scores = sorted(scores, key=lambda item: item[1], reverse=True)
    embed = Embed(colour=Colour.blurple())
    embed.title = "Lobby Rankings"
    rank = 1
    for user_id, score in scores:
        user = lobby.bot.get_user(user_id)
        if user is None:
            continue

        if filter_lobby and Player(user) not in lobby.players:
            continue

        embed.add_field(name=f"{rank}. {user}", value=score, inline=False)
        rank += 1

    if len(embed.fields) == 0:
        text = "No players in the lobby (or channel) have a ranking."
        embed.add_field(name="No players", value=text)

    await ctx.send(embed=embed)
