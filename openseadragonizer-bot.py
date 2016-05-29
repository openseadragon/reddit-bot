import sys
import logging
import praw
import time
import traceback
import sqlite3
from prawoauth2 import PrawOAuth2Mini
from settings import app_key, app_secret, access_token, refresh_token, scopes

logging.basicConfig(filename = 'bot.log', level=logging.INFO)
logging.info('Starting openseadragonizer reddit bot.')

db_conn = sqlite3.connect('sqlite.db')
db_cursor = db_conn.cursor()

db_cursor.execute("CREATE TABLE IF NOT EXISTS processed_submissions " + \
                  "(id TEXT PRIMARY KEY)")
db_conn.commit()
logging.info('SQLite connection initialized.')


subreddit = 'earthporn+mapporn+space'

user_agent = "OpenSeadragonizer:v0.0.0 (by /u/openseadragonizer)"
r = praw.Reddit(user_agent = user_agent)
oauth_helper = PrawOAuth2Mini(r, app_key=app_key, app_secret=app_secret,
    access_token=access_token, refresh_token=refresh_token, scopes=scopes)
logging.info('OAuth connection ready.')

min_width = 2000
min_height = 2000

def get_message(url):
    return "[Zoomable version of the image]" + \
           "(https://openseadragon.github.io/openseadragonizer/?img=" + url + \
           ")\n\n&nbsp;\n\n---\n" + \
           "I'm a bot, please report any issue on " + \
           "[GitHub](https://github.com/openseadragon/reddit-bot/issues)."

while True:
    try:
        submissions = r.get_subreddit(subreddit).get_new(limit = 100)
        for submission in submissions:
            if hasattr(submission, 'preview') and \
                submission.preview['images'] and \
                db_cursor.execute("SELECT id FROM processed_submissions WHERE id=(?)",\
                    (submission.id,)).fetchone() is None:
                source = submission.preview['images'][0]['source']
                if source['width'] > min_width or source['height'] > min_height:
                    message = get_message(source['url'])
                    submission.add_comment(message)
                    db_cursor.execute("INSERT INTO processed_submissions(id) VALUES (?)",\
                        (submission.id,))
                    db_conn.commit()
                    logging.info("Posted comment in submission titled " +  submission.title)
        logging.info('Going to sleep')
        time.sleep(30)
    except praw.errors.OAuthInvalidToken:
        # token expired, refresh 'em!
        oauth_helper.refresh()
        logging.info('Token refreshed')
    except Exception:
        logging.exception('Unexpected exception, going to sleep.')
        time.sleep(30)
