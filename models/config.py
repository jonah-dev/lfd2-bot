import re
import yaml
import inspect

from typing import Any, Callable, Dict, List, Optional

DIRECTIVE = re.compile(r"^\s*@(?P<directive>.*)\((?P<props>.*)\)\s*$", re.M)

ALL_DIRECTIVES: Dict[str, Callable] = {}


def directive(fn):
    ALL_DIRECTIVES[fn.__name__] = fn


class Config:
    def __init__(self, topic: str):
        self.vMax: Optional[int] = None
        self.vMin: Optional[int] = None
        self.vOverflow: bool = True
        self.vTeams: Optional[List[int]] = None

        self.issues = {}

        try:
            self.install(Config.parse(topic))
        except Exception:
            self.issue(
                "Error parsing topic."
                + " Directives must start on their own line: Ex: @players(...)"
            )

    @staticmethod
    def parse(topic: str) -> Dict[str, any]:
        lines = DIRECTIVE.findall(topic)
        return {d: p for [d, p] in lines}

    def install(self, directives):
        for d in directives:
            try:
                if d in ALL_DIRECTIVES:
                    props = directives[d]
                    installer = ALL_DIRECTIVES[d]
                    installer(self, props)
                else:
                    self.issue(f"Unknown directive: {d}")
            except Exception:
                self.issue(f"Error installing directive: {d}")

    # -- Directives -----------------------------------------------------------

    @directive
    def players(self, props: str):
        props = self.parseMulti(props)
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
        props = self.parseSingle(props)
        if type(props) is not list:
            self.issue("You must provide a list of teams. Ex: [4, 4]")
            return

        if any(type(p) is not int for p in props):
            self.issue("You must provide a list of teams. Ex: [4, 4]")
            return

        self.vTeams = props

    @directive
    def overflow(self, props: str):
        props = self.parseSingle(props)
        if type(props) is not bool:
            self.issue("You must provide either True or False.")
            return

        self.vOverflow = props

    # -- Helpers --------------------------------------------------------------

    @staticmethod
    def parseSingle(props: str) -> Optional[Any]:
        try:
            return yaml.load(props)
        except Exception:
            return None

    @staticmethod
    def parseMulti(props: str) -> Optional[Dict[str, Any]]:
        return Config.parseSingle("{" + props + "}")

    def issue(self, message: str, skip_frames: int = 1):
        area = inspect.stack()[skip_frames].function
        records = self.issues.get(area, [])
        records.append(message)
        self.issues[area] = records
