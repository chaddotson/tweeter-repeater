#!/usr/bin/env python3

from argparse import ArgumentParser
from configparser import ConfigParser
from logging import basicConfig, DEBUG, INFO, getLogger
from os import getcwd
from os.path import join
from tweepy import Cursor

from pytools.twitter.api import create_api
from pytools.util.persistance import PersistentDict


logger = getLogger(__name__)

since_id_name="since_id"


def run(args):
    logging_config = dict(level=INFO, format='[%(asctime)s - %(filename)s:%(lineno)d - %(funcName)s - %(levelname)s] %(message)s')
    basicConfig(**logging_config)

    logger.debug("Reading config file, %s", args.settings)

    config = ConfigParser()
    config.read(args.settings)

    logger.debug("Read config file")

    query = " OR ".join(config.get("app", "hashtags").split(", "))
    max_results = config.getint("app", "max_results")
    rt_msg = config.get("app", "rt_msg")
    session_file = config.get("app", "session_file")
    session_file = session_file.format(cwd=getcwd())

    logger.debug("query=%s", query)
    logger.debug("max_results=%d", max_results)
    logger.debug("rt_msg=%s", rt_msg)
    logger.debug("session_file=%s", session_file)

    persist = PersistentDict(session_file)
    since_id = persist.get(since_id_name, None)
    logger.debug("Retrieved since_id %s", since_id)

    twitter_api = create_api(config.get("twitter", "consumer_key"),
                             config.get("twitter", "consumer_secret"),
                             config.get("twitter", "access_key"),
                             config.get("twitter", "access_secret"))

    search = Cursor(twitter_api.search, q=query, since_id=since_id)

    format = "{msg} https://twitter.com/{screen_name}/status/{status_id}"


    results = search.items(max_results)

    for tweet in results:
        msg = format.format(msg=rt_msg, screen_name=tweet.author.screen_name, status_id=tweet.id)

        logger.info("tweeting: %s", msg)

        try:
            twitter_api.update_status(msg)
        except:
            logger.exception("Error posting tweet!")

    if len(results.page_iterator.results) > 1:

        logger.info("Saving last id %s", results.page_iterator.results[0].since_id)
        persist[since_id_name] = results.page_iterator.results[0].since_id

    persist.sync()



def create_ini(filename):
    config = ConfigParser()

    config.add_section("app")
    config.set("app", "hashtags", "")
    config.set("app", "max_results", "10")
    config.set("app", "rt_msg", "RT")
    config.set("app", "session_file", join(getcwd(), "state.sav"))

    config.add_section("twitter")
    config.set("twitter", "consumer_key", "")
    config.set("twitter", "consumer_secret", "")
    config.set("twitter", "access_key", "")
    config.set("twitter", "access_secret", "")

    with open(filename, "w") as f:
        config.write(f)


def parse_args():
    parser = ArgumentParser(description='Weather Tweeter')
    parser.add_argument('settings', help='Settings file', nargs='?', default=join(getcwd(), "settings.ini"))
    parser.add_argument('-c', '--create', help='Create settings file', default=False, action='store_true')
    parser.add_argument('-v', '--verbose', help='Verbose logs', default=False, action='store_true')

    return parser.parse_args()


def main():
    args = parse_args()
    if args.verbose:
        getLogger('').setLevel(DEBUG)

    if not args.create:
        run(args)
    else:
        create_ini(args.settings)


if __name__ == "__main__":
    main()

