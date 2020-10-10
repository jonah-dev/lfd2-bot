from typing import List
from models.player import Player
from discord import TextChannel


class UsageException(Exception):
    def __init__(self, ctx: TextChannel, message: str):
        self.ctx = ctx
        self.message = message
        super().__init__(self.message)

    async def notice(self):
        await self.ctx.send(self.message)

    @staticmethod
    def adder_must_join(channel: TextChannel):
        return UsageException(
            channel, "You must be in the lobby to add other players."
        )

    @staticmethod
    def leaver_not_added(channel: TextChannel):
        return UsageException(
            channel,
            "This player has recently left the lobby and"
            " cannot be added back by other players.",
        )

    @staticmethod
    def game_is_full(channel: TextChannel):
        return UsageException(
            channel,
            "Sorry the game is full. Please wait for someone to unready.",
        )

    @staticmethod
    def already_joined(channel: TextChannel, from_other: bool):
        if from_other:
            return UsageException(
                channel, "This player is already in the lobby."
            )

        return UsageException(channel, "You are already in the lobby.")

    @staticmethod
    def not_in_lobby(channel: TextChannel, player: Player):
        return UsageException(
            channel, f"This player is not in the lobby: {player.get_name()}"
        )

    @staticmethod
    def empty_lobby(channel: TextChannel):
        return UsageException(channel, "The lobby is empty.")

    @staticmethod
    def join_the_lobby_first(channel: TextChannel):
        return UsageException(channel, "Join the lobby with `?join`.")

    @staticmethod
    def already_ready(channel: TextChannel):
        return UsageException(
            channel,
            "You are already marked as ready. I can tell that you're eager.",
        )

    @staticmethod
    def not_enough_for_match(channel: TextChannel):
        return UsageException(
            channel, "You need 8 ready players to start a match."
        )

    @staticmethod
    def seen_all_matches(channel: TextChannel):
        return UsageException(
            channel, "You've already seen all possible matches"
        )

    @staticmethod
    def lobby_already_started(channel: TextChannel):
        return UsageException(
            channel,
            "The lobby has already been started."
            " You can restart the lobby with `?reset`.",
        )

    @staticmethod
    def directive_missing(channel: TextChannel, directive: str):
        return UsageException(
            channel,
            f"Please specify `@{directive}(...)` in the channel topic.",
        )

    @staticmethod
    def game_sheet_not_loaded(channel: TextChannel, url: str):
        return UsageException(
            channel,
            "The following sheet could not be loaded or parsed." f"\n{url}",
        )

    @staticmethod
    def unexpected_option(
        channel: TextChannel,
        actual: str,
        expected: List[str],
    ):
        expected = ", ".join(expected)
        return UsageException(
            channel,
            f"Unexpected option provided: {actual}"
            f"\nExpected one of [{expected}]",
        )
