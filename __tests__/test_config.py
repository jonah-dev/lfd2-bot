from aiounittest import AsyncTestCase

from models.config import Config


class TestConfig(AsyncTestCase):
    async def test_parse_single(self):
        topic = """
            @int(123)
            @float(4.56)
            @bool(true)
            @string("foo")
        """
        c = Config.parse(topic)
        assert Config.parseSingle(c["int"]) == 123
        assert Config.parseSingle(c["float"]) == 4.56
        assert Config.parseSingle(c["bool"])
        assert Config.parseSingle(c["string"]) == "foo"

    async def test_parse_multi(self):
        topic = """
            @foo(int: 123, float: 4.56, bool: true, string: "foo")
        """
        c = Config.parse(topic)
        c = Config.parseMulti(c["foo"])
        assert c["int"] == 123
        assert c["float"] == 4.56
        assert c["bool"]
        assert c["string"] == "foo"

    async def test_parse_hard(self):
        topic = """
            @foo(comma: ",", colon: ":", escape: "\"")
        """
        Config.parse(topic)

    async def test_parse_str(self):
        topic = """
            @quote('foo')
            @doublequote("foo")
            @noquote(foo)
        """
        c = Config.parse(topic)
        assert Config.parseSingle(c["quote"]) == "foo"
        assert Config.parseSingle(c["doublequote"]) == "foo"
        assert Config.parseSingle(c["noquote"]) == "foo"

    async def test_parse_bool(self):
        topic = """
            @TRUE(TRUE)
            @True(True)
            @true(true)
            @tRuE(tRuE)
            @FALSE(FALSE)
            @False(False)
            @false(false)
            @FaLsE(FaLsE)
        """
        c = Config.parse(topic)
        v = Config.parseSingle(c["TRUE"])
        assert type(v) is bool and v
        v = Config.parseSingle(c["True"])
        assert type(v) is bool and v
        v = Config.parseSingle(c["true"])
        assert type(v) is bool and v

        v = Config.parseSingle(c["FALSE"])
        assert type(v) is bool and not v
        v = Config.parseSingle(c["False"])
        assert type(v) is bool and not v
        v = Config.parseSingle(c["false"])
        assert type(v) is bool and not v

    async def test_config_amongus(self):
        topic = """
            @players(min: 6, max: 10)
            @overflow(true)
        """
        c = Config(topic)
        assert c.vMax == 10
        assert c.vMin == 6
        assert c.vOverflow
        assert not c.vTeams

    async def test_config_warzone(self):
        topic = """
            @players(min: 1, max: 4)
            @overflow(false)
        """
        c = Config(topic)
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
        c = Config(topic)
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
        c = Config(topic)
        assert c.vMax == 5
        assert c.vMin == 4
        assert c.vOverflow
        assert c.vTeams == [4, 1]
