from utils.directive import directive
import utils.directive as directives
import inspect

from typing import Callable, List, Optional, Tuple

from discord.channel import TextChannel
from discord.ext.commands import Bot


class Config:
    def __init__(self, topic: str, bot: Bot, installCommand: Callable):
        import plugins.SuperCashBrosLeftForDead.SuperCashBrosLeftForDead  # noqa F401

        self.bot = bot
        self.installCommand = installCommand

        self.vMax: Optional[int] = None
        self.vMin: int = 0
        self.vOverflow: bool = True
        self.vTeams: Optional[List[int]] = None
        self.vBroadcastChannels: List = list()

        self.issues = {}

        try:
            self.install(directives.parse_directives(topic))
        except Exception:
            self.issue(
                "Error parsing topic."
                + " Directives must start on their own line: Ex: @players(...)"
            )

    def install(self, directives: List[Tuple[Callable, str]]):
        for installer, props in directives:
            try:
                installer(self, props)
            except Exception:
                self.issue(f"Error installing directive: {installer.__name__}")

    # -- Directives -----------------------------------------------------------

    @directive
    def players(self, props: str):
        props = directives.parse_multi(props)
        if type(props) is not dict:
            self.issue("You must provide a value. Ex: `{min: 8, max: 10`}")
            return

        minimum = props.get("min")
        if minimum is not None and type(minimum) is not int:
            self.issue("**Min** must be a number. Ex: `min: 8`")
        self.vMin = minimum

        maximum = props.get("max")
        if maximum is not None and type(maximum) is not int:
            self.issue("**Max** must be a number. Ex: `max: 8`")
        self.vMax = maximum

    @directive
    def teams(self, props: str):
        props = directives.parse_single(props)
        if type(props) is not list:
            self.issue("You must provide a list of teams. Ex: [4, 4]")
            return

        if any(type(p) is not int for p in props):
            self.issue("You must provide a list of teams. Ex: [4, 4]")
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

    def issue(self, message: str, skip_frames: int = 1):
        area = inspect.stack()[skip_frames].function
        records = self.issues.get(area, [])
        records.append(message)
        self.issues[area] = records
