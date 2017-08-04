import datetime
import random
import requests

from bson.son import SON

from helga import log
from helga.db import db
from helga.plugins import Command

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


class OralHistory(Command):

    command = 'oral'

    def preprocess(self, client, channel, nick, message):
        redacted_message = redact(message)

        db.logger.insert({
            'channel': channel,
            'nick': nick,
            'message': redacted_message,
            'timestamp': datetime.datetime.utcnow(),
        })

        return (channel, nick, redacted_message)


    def run(self, client, channel, nick, message, cmd, args):

        logger.debug('args: {}'.format(args))

        if len(args):

            if args[0] == 'top':

                pipeline = [
                    { '$match': { 'channel': channel,
                }},
                    { '$group': {'_id': '$nick', 'count': {'$sum': 1}}},
                    { '$sort': SON([('count', -1), ('_id', -1)])}
                ]

                if len(args) > 1:
                    start_date = datetime.datetime.utcnow()

                    if args[1] == 'day':
                        start_date -= datetime.timedelta(days=1)
                    elif args[1] == 'week':
                        start_date -= datetime.timedelta(days=7)

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

            if args[0] == 'search':

                pipeline = [{
                    '$match': {
                        'message': {'$regex': ' '.join(args[1:])},
                        'channel': channel
                    }},
                ]

                dpaste_doc = ''

                for result in db.logger.aggregate(pipeline):
                    if result['message'].startswith('oral search', 1):
                        continue
                    dpaste_doc += u'<{}> {}\n'.format(result['nick'], result['message'])

                if dpaste_doc:
                    payload = {
                        'content': dpaste_doc,
                        'syntax': 'irc',
                        'expiry_days':'1',
                    }

                    resp = requests.post(
                        'http://dpaste.com/api/v2/',
                        data=payload,
                    )

                    return resp.content

                else:
                    return 'no results'
