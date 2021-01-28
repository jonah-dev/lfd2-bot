from utils.directive import directive
import utils.directive as directives
import inspect

from typing import Callable, List, Optional

from discord.channel import TextChannel
from discord.ext.commands import Bot


class Config:
    def __init__(
        self, channel: TextChannel, bot: Bot, installCommand: Callable
    ):
        import plugins.SuperCashBrosLeftForDead.SuperCashBrosLeftForDead  # noqa F401

        self.bot = bot
        self.installCommand = installCommand

        self.vName: str = f"#{channel.name}"
        self.vMax: Optional[int] = None
        self.vMin: int = 0
        self.vOverflow: bool = True
        self.vTeams: Optional[List[int]] = None
        self.vBroadcastChannels: List = list()

        self.issues = {}

        self.install(channel.topic)

    def install(self, update: str):
        for installer, props in directives.parse_directives(update):
            if installer is None:
                self.issue(f"Unknown directive: {props}", area="General")
                continue

            try:
                self.issues.pop(f"@{installer.__name__}", None)
                installer(self, props)
            except Exception:
                self.issue(
                    f"Failed installing: `@{installer}({props})`", "General"
                )

    # -- Directives -----------------------------------------------------------

    @directive
    def name(self, props: str):
        props = directives.parse_single(props)
        if type(props) is not str:
            self.issue("You must provide a value, Ex: `'Game night!'`")
            return

        self.vName = props

    @directive
    def players(self, props: str):
        props = directives.parse_multi(props)
        if type(props) is not dict:
            self.issue("You must provide a value. Ex: `{min: 8, max: 10`}")
            return

        minimum = props.get("min")
        if minimum is not None and type(minimum) is not int:
            self.issue("The value of `min` must be a number. Ex: `min: 8`")
        self.vMin = minimum

        maximum = props.get("max")
        if maximum is not None and type(maximum) is not int:
            self.issue("The value of `Max` must be a number. Ex: `max: 8`")
        self.vMax = maximum

        if minimum is None and maximum is None:
            self.issue("You must provided `min` and/or `Max`.")

    @directive
    def teams(self, props: str):
        props = directives.parse_single(props)
        if type(props) is not list:
            self.issue("You must provide a list of teams. Ex: `[4, 4]`")
            return

        if any(type(p) is not int for p in props):
            self.issue("You must provide a list of teams. Ex: `[4, 4]`")
            return

        self.vTeams = props

    @directive
    def overflow(self, props: str):
        props = directives.parse_single(props)
        if type(props) is not bool:
            self.issue("You must provide either True or False.")
            return

        self.vOverflow = props

    @directive
    def broadcast(self, props: str):
        props = directives.parse_single(props)
        if type(props) is str:
            destinations = list(props)
        elif type(props) is list:
            destinations = props
        else:
            self.issue("You must provide the channel name(s)")
            return

        all_channels = self.bot.get_all_channels()
        for dest in destinations:
            matching = list(filter(lambda c: c.name == dest, all_channels))
            if not len(matching):
                self.issue(f"'{dest}' is not a visible text channel")

            for channel in matching:
                if not isinstance(channel, TextChannel):
                    self.issue(f"'{dest}' is not a text channel")
                else:
                    self.vBroadcastChannels.append(channel)

    # -- Helpers --------------------------------------------------------------

    def issue(self, message: str, *, skip_frames: int = 1, area: str = None):
        if not area:
            area = f"@{inspect.stack()[skip_frames].function}"

        records = self.issues.get(area, [])
        records.append(message)
        self.issues[area] = records
