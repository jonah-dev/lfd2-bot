from aiounittest import AsyncTestCase
from requests import head

from utils.get_steam_icon import get_steam_icon


class TestGetSteamIcon(AsyncTestCase):
    def test_get(self):
        url = get_steam_icon(550)
        assert url is not None
        headers = head(url).headers
        assert headers.get("Content-Type") == "image/jpeg"
        assert int(headers.get("Content-Length")) > 0

    def test_fail(self):
        url = get_steam_icon(-1)
        assert url is None
