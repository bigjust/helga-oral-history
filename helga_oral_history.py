import datetime
import random
import re
import urllib.parse
import urllib.request

from helga import log
from helga.db import get_connection
from helga.plugins import Command

logger = log.getLogger(__name__)

# Table for the message log — created lazily on first DB use
_LOG_TABLE = "oral_history_log"

# ponytail: naive bracket redaction, no nesting or escape handling
_BRACKET_RE = re.compile(r'\[[^\]]*\]')


def _ensure_table(conn):
    with conn.cursor() as cur:
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {_LOG_TABLE} (
                id SERIAL PRIMARY KEY,
                channel TEXT NOT NULL,
                nick TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
    conn.commit()


def redact(message):
    """Replace anything inside [...] with [REDACTED]."""
    return _BRACKET_RE.sub('[REDACTED]', message)


def obfuscate_nick(nick):
    """Replace a random character with '_' to prevent highlighting."""
    if not nick:
        return nick
    index = random.randrange(len(nick))
    return nick[:index] + '_' + nick[index + 1:]


class OralHistory(Command):

    command = 'oral'

    def preprocess(self, client, channel, nick, message):
        redacted_message = redact(message)

        conn = get_connection()
        if conn is not None:
            _ensure_table(conn)
            with conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO {_LOG_TABLE} (channel, nick, message, timestamp) "
                    "VALUES (%s, %s, %s, %s)",
                    (channel, nick, redacted_message, datetime.datetime.utcnow()),
                )
            conn.commit()

        return channel, nick, redacted_message

    def run(self, client, channel, nick, message, cmd, args):
        logger.debug('args: %s', args)

        if not args:
            return

        conn = get_connection()
        if conn is None:
            return 'database unavailable'

        if args[0] == 'top':
            start_date = None
            if len(args) > 1:
                start_date = datetime.datetime.utcnow()
                if args[1] == 'day':
                    start_date -= datetime.timedelta(days=1)
                elif args[1] == 'week':
                    start_date -= datetime.timedelta(days=7)

            with conn.cursor() as cur:
                if start_date:
                    cur.execute(
                        f"SELECT nick, COUNT(*) AS count FROM {_LOG_TABLE} "
                        "WHERE channel = %s AND timestamp >= %s "
                        "GROUP BY nick ORDER BY count DESC, nick DESC LIMIT 5",
                        (channel, start_date),
                    )
                else:
                    cur.execute(
                        f"SELECT nick, COUNT(*) AS count FROM {_LOG_TABLE} "
                        "WHERE channel = %s "
                        "GROUP BY nick ORDER BY count DESC, nick DESC LIMIT 5",
                        (channel,),
                    )
                top_5 = cur.fetchall()

            logger.debug('top_5: %s', top_5)

            for i, row in enumerate(top_5):
                client.msg(channel, '{}. {} [{}]'.format(
                    i + 1,
                    obfuscate_nick(row['nick']),
                    row['count'],
                ))

        if args[0] == 'search':
            search_term = ' '.join(args[1:])

            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT nick, message FROM {_LOG_TABLE} "
                    "WHERE message ~ %s AND channel = %s "
                    "ORDER BY timestamp",
                    (search_term, channel),
                )
                results = cur.fetchall()

            dpaste_doc = ''
            for row in results:
                if row['message'].startswith('oral search', 1):
                    continue
                dpaste_doc += '<{}> {}\n'.format(row['nick'], row['message'])

            if dpaste_doc:
                data = urllib.parse.urlencode({
                    'content': dpaste_doc,
                    'syntax': 'irc',
                    'expiry_days': '1',
                }).encode()
                resp = urllib.request.urlopen(
                    'http://dpaste.com/api/v2/', data=data
                )
                return resp.read().decode()
            else:
                return 'no results'
