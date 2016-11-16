import datetime

from helga.db import db
from helga.plugins import preprocessor


def redact(message):
    """
    Takes str `message` and returns the same string but with anything
    in []s as [REDACTED]
    """

    return message

@preprocessor
def oral_history(client, channel, nick, message):

    redacted_message = redact(message)

    db.logger.insert({
        'channel': channel,
        'nick': nick,
        'message': redacted_message,
        'timestamp': datetime.datetime.utcnow(),
    })

    return (channel, nick, redacted_message)
