from typing import Any, Dict

from discord.channel import TextChannel
from .usage_exception import UsageException


def option_switch(channel: TextChannel, option, cases: Dict[str, Any]):
    if option not in cases:
        if len(cases) and None in cases:
            options = ["None"]
        else:
            options = filter(cases.keys())
        raise UsageException.unexpected_option(channel, options)

    return cases[option]
