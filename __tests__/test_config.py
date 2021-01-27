from aiounittest import AsyncTestCase
from unittest.mock import AsyncMock, patch

from discord.ext.commands.bot import Bot

from models.config import Config
from utils.directive import (
    parse_directives,
    parse_single,
    parse_multi,
    ALL_DIRECTIVES,
)


def bot() -> Bot:
    bot = AsyncMock(spec=Bot)
    return bot


def noop():
    pass


TEST_DIRECTIVES = {
    "int": noop,
    "float": noop,
    "bool": noop,
    "string": noop,
    "foo": noop,
    "quote": noop,
    "doublequote": noop,
    "noquote": noop,
    "TRUE": noop,
    "True": noop,
    "true": noop,
    "tRuE": noop,
    "FALSE": noop,
    "False": noop,
    "false": noop,
    "FaLsE": noop,
}

PATCH_DIRECTIVES = {**ALL_DIRECTIVES, **TEST_DIRECTIVES}


@patch("utils.directive.ALL_DIRECTIVES", PATCH_DIRECTIVES)
class TestConfig(AsyncTestCase):
    async def test_parse_single(self):
        topic = """
            @int(123)
            @float(4.56)
            @bool(true)
            @string("foo")
        """
        c = parse_directives(topic)
        assert parse_single(next(c)[1]) == 123
        assert parse_single(next(c)[1]) == 4.56
        assert parse_single(next(c)[1])
        assert parse_single(next(c)[1]) == "foo"

    async def test_parse_multi(self):
        topic = """
            @foo(int: 123, float: 4.56, bool: true, string: "foo")
        """
        c = parse_directives(topic)
        props = parse_multi(next(c)[1])
        assert props["int"] == 123
        assert props["float"] == 4.56
        assert props["bool"]
        assert props["string"] == "foo"

    async def test_parse_hard(self):
        topic = """
            @foo(comma: ",", colon: ":", escape: '"')
        """
        c = parse_directives(topic)
        props = parse_multi(next(c)[1])
        assert props["comma"] == ","
        assert props["colon"] == ":"
        assert props["escape"] == '"'

    async def test_parse_str(self):
        topic = """
            @quote('foo')
            @doublequote("foo")
            @noquote(foo)
        """
        c = parse_directives(topic)
        assert parse_single(next(c)[1]) == "foo"
        assert parse_single(next(c)[1]) == "foo"
        assert parse_single(next(c)[1]) == "foo"

    async def test_parse_bool(self):
        topic = """
            @TRUE(TRUE)
            @True(True)
            @true(true)
            @FALSE(FALSE)
            @False(False)
            @false(false)
        """
        c = parse_directives(topic)
        v = parse_single(next(c)[1])
        assert type(v) is bool and v
        v = parse_single(next(c)[1])
        assert type(v) is bool and v
        v = parse_single(next(c)[1])
        assert type(v) is bool and v

        v = parse_single(next(c)[1])
        assert type(v) is bool and not v
        v = parse_single(next(c)[1])
        assert type(v) is bool and not v
        v = parse_single(next(c)[1])
        assert type(v) is bool and not v

    async def test_config_amongus(self):
        topic = """
            @players(min: 6, max: 10)
            @overflow(true)
        """
        c = Config(topic, bot(), noop)
        assert c.vMax == 10
        assert c.vMin == 6
        assert c.vOverflow
        assert not c.vTeams

    async def test_config_warzone(self):
        topic = """
            @players(min: 1, max: 4)
            @overflow(false)
        """
        c = Config(topic, bot(), noop)
        assert c.vMax == 4
        assert c.vMin == 1
        assert not c.vOverflow
        assert not c.vTeams

    async def test_config_left_for_dead(self):
        topic = """
            @overflow(true)
            @players(min: 8, max: 8)
            @teams([4, 4])
        """
        c = Config(topic, bot(), noop)
        assert c.vMax == 8
        assert c.vMin == 8
        assert c.vOverflow
        assert c.vTeams == [4, 4]

    async def test_config_dead_by_daylight(self):
        topic = """
            @teams([4, 1])
            @players(min: 4, max: 5)
            @overflow(true)
        """
        c = Config(topic, bot(), noop)
        assert c.vMax == 5
        assert c.vMin == 4
        assert c.vOverflow
        assert c.vTeams == [4, 1]
