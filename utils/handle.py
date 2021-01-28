import logging
from traceback import TracebackException
from typing import Optional

from discord.ext.commands.context import Context
from discord.ext.commands.errors import UnexpectedQuoteError

from utils.usage_exception import UsageException

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("LFD2Bot")


async def handle(context: Optional[Context], exception: BaseException):
    if isinstance(exception, UsageException):
        await exception.notice()
        return

    if isinstance(exception.__cause__, UsageException):
        await exception.__cause__.notice()
        return

    if isinstance(exception, UnexpectedQuoteError):
        await UsageException.argument_quote_issue(context.channel).notice()
        return

    if exception.__cause__ is not None:
        trace = TracebackException.from_exception(exception.__cause__)
    else:
        trace = TracebackException.from_exception(exception)

    stack = "".join(trace.format())
    if context is not None:
        await context.send("There was an error during your command :worried:")
        logger.error('Command: "%s"\n%s', context.message.content, stack)
        return

    logger.error("Command: <unkown>\n%s", stack)
