import logging
import traceback
from typing import Optional, Text

from discord.channel import TextChannel

from utils.usage_exception import UsageException

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("LFD2Bot")


async def handle(channel: Optional[TextChannel], exception: BaseException):
    if isinstance(exception, UsageException):
        await exception.notice()
        return

    if isinstance(exception.__cause__, UsageException):
        await exception.__cause__.notice()
        return

    if exception.__cause__ is not None:
        trace = traceback.TracebackException.from_exception(exception.__cause__)
    else:
        trace = traceback.TracebackException.from_exception(exception)

    pretty_trace = "".join(trace.format())
    if channel is TextChannel:
        await channel.send("There was an error during your command :worried:")
        logger.error('Command: "%s"\n%s', channel.message.content, pretty_trace)
        return
    
    logger.error('Command: <unkown>\n%s', pretty_trace)

