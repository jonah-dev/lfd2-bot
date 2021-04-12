from plugins.SuperCashBrosLeftForDead.season import Season
from models.player import Player
from plugins.SuperCashBrosLeftForDead.ranker import get_ranks
from plugins.SuperCashBrosLeftForDead.game_data import GameData
from discord.ext.commands import Bot
from unittest.mock import AsyncMock
from aiounittest.case import AsyncTestCase
from discord import Member, TextChannel

SHEETS = "1886KNfDRp-RGRnRkAbb8IQHTvQFHw_xcavz_2pXmIsg"


def bot() -> Bot:
    bot = AsyncMock(spec=Bot)

    def get_user(id):
        name = PEOPLE[id]
        return real_member(name, id)

    bot.get_user = get_user
    return bot


def channel(topic: str = "") -> TextChannel:
    channel = AsyncMock(spec=TextChannel)
    channel.id = 1234
    channel.topic = topic
    channel.mention = 1234

    return channel


def real_member(name: str, id: int) -> Member:
    member = AsyncMock(spec=Member)
    member.id = id
    member.display_name = name
    member.mention = name
    member.bot = None
    return member


class TestBench(AsyncTestCase):
    async def test_print_season_ranks(self):
        players = [Player(real_member(PEOPLE[id], id)) for id in PEOPLE]
        games = await GameData.fetch(
            "1886KNfDRp-RGRnRkAbb8IQHTvQFHw_xcavz_2pXmIsg", channel()
        )

        ranks = get_ranks(games, Season.current())
        players.sort(key=lambda p: ranks.get(p.member.id, 0), reverse=True)
        for i, p in enumerate(players):
            print(f"{i}.) [{ranks.get(p.member.id, None)}] {p.get_name()}")


PEOPLE = {
    196141130230923264: "AJ",
    272297006503034881: "Alex E",
    94956978182303744: "Alex S",
    234531070823890946: "Anton",
    216700608374243328: "Ben",
    -1: "Booi",
    135818592682770432: "Brinsko",
    -2: "Burncycle",
    276558643158056971: "Christian",
    581717254090260490: "Cullen",
    364944510905483265: "Dan",
    192484843664179200: "Derek",
    398204819308806182: "Duncan",
    -3: "Eric",
    508016750051328020: "Ian",
    269894533024579584: "Jack",
    236938533179228162: "Joe D",
    364557831443316738: "Joe G",
    147788154831634434: "Jonah",
    410759955780730880: "Josh",
    -4: "Kevin",
    398205054991204353: "Kyle",
    404099743078285322: "Kyle K",
    457339396728029195: "Maddy",
    273660995057221636: "Mano",
    117113284959797255: "Mason",
    369205307680751650: "Myat",
    264864307550879744: "Pat",
    320709461318565889: "Tommy",
    138516611316318208: "Westy",
    137286850111995904: "Zaruba",
    280492678137905152: "Casey D",
    151856271287386112: "Jake",
}
