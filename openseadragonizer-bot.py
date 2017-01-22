import sys
import logging
import praw
import time
import traceback
import sqlite3
import urllib.parse
from settings import app_key, app_secret, access_token, refresh_token, scopes

logging.basicConfig(
    format = '[%(asctime)s] %(levelname)s: %(name)s: %(message)s',
    filename = 'bot.log',
    level=logging.INFO)
logging.info('Starting openseadragonizer reddit bot.')

db_conn = sqlite3.connect('sqlite.db')
db_cursor = db_conn.cursor()

db_cursor.execute("CREATE TABLE IF NOT EXISTS processed_submissions " + \
                  "(id TEXT PRIMARY KEY)")
db_conn.commit()
logging.info('SQLite connection initialized.')

subreddits = ['mapporn', 'warshipporn', 'warplaneporn']
subreddit = '+'.join(subreddits)

user_agent = "OpenSeadragonizer:v0.0.0 (by /u/openseadragonizer)"
r = praw.Reddit(
    client_id = app_key,
    client_secret = app_secret,
    refresh_token = refresh_token,
    user_agent = user_agent)

min_width = 2000
min_height = 2000

def get_message(url):
    encoded_url = urllib.parse.quote(url.encode('utf-8'), safe='~()*!.\'')
    return "[Zoomable version of the image]" + \
           "(https://openseadragon.github.io/openseadragonizer/?img=" + \
           encoded_url + "&encoded=true" + ")\n\n&nbsp;\n\n---\n" + \
           "I'm a bot, please report any issue or feature request on " + \
           "[GitHub](https://github.com/openseadragon/reddit-bot/issues)."

while True:
    try:
        submissions = r.subreddit(subreddit).new(limit = 100)
        for submission in submissions:
            if hasattr(submission, 'preview') and \
                submission.preview['images'] and \
                db_cursor.execute("SELECT id FROM processed_submissions WHERE id=(?)",\
                    (submission.id,)).fetchone() is None:
                source = submission.preview['images'][0]['source']
                if source['width'] > min_width or source['height'] > min_height:
                    try:
                        message = get_message(source['url'])
                        submission.reply(message)
                        db_cursor.execute("INSERT INTO processed_submissions(id) VALUES (?)",\
                            (submission.id,))
                        db_conn.commit()
                        logging.info("Posted comment in submission titled " +  submission.title)
                    except Exception:
                        logging.exception("Could not post comment in submission titled " + submission.title)
        logging.info('Going to sleep')
        time.sleep(30)
    except Exception:
        logging.exception('Unexpected exception, going to sleep.')
        time.sleep(30)
