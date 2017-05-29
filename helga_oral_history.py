import datetime
import random

from bson.son import SON

from helga import log
from helga.db import db
from helga.plugins import preprocessor, command

logger = log.getLogger(__name__)


def redact(message):
    """
    Takes str `message` and returns the same string but with anything
    in []s as [REDACTED]
    """

    return message

def obfuscate_nick(nick):
    """
    Replaces a random character with a '_' to prevent highlighting.
    """

    index = random.randrange(len(nick))

    return nick[:index] + '_' + nick[index+1:]

@preprocessor
@command('oral', help='oral history leaderboard')
def oral_history(client, channel, nick, message, *args):
    """

    Dual Preprocessor/Command.

    Command handles search/stats, while the preprocessor handles
    logging statements.

    Preprocessor:

    Redacts message and stores in mongo w/ nick, channel, message and
    timestamp.

    Command:
    Returns top 5 prolific irc'ers

    usage: ,oral [day|week|search] [<search_pattern>]
    """

    if len(args) == 0:

        redacted_message = redact(message)

        db.logger.insert({
            'channel': channel,
            'nick': nick,
            'message': redacted_message,
            'timestamp': datetime.datetime.utcnow(),
        })

        return (channel, nick, redacted_message)


    # leaderboard

    pipeline = [
            { '$match': { 'channel': channel,
            }},
            { '$group': {'_id': '$nick', 'count': {'$sum': 1}}},
            { '$sort': SON([('count', -1), ('_id', -1)])}
        ]

    if len(args[1]) == 1:

        start_date = datetime.datetime.utcnow()
        #return args[1]

        logger.debug('args: {}'.format(args))

        if args[1][0] == 'day':
            start_date -= datetime.timedelta(days=1)

        elif args[1][0] == 'week':
            start_date -= datetime.timedelta(days=7)

        logger.debug('start_date: {}'.format(start_date))

        pipeline[0]['$match']['timestamp'] = { '$gte': start_date }

    top_5 = [nick for nick in db.logger.aggregate(pipeline)][:5]

    logger.debug('top_5: {}'.format(top_5))

    place = 0
    for nick in top_5:
        client.msg(channel, '{}. {} [{}]'.format(
            place + 1,
            obfuscate_nick(top_5[place]['_id']),
            top_5[place]['count'],
        ))
        place += 1
