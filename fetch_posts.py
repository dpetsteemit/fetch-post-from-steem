# Original Source Code from https://github.com/emre/tagbot
# Run and maintain by team @dpet on steemit

import argparse
import json
import logging
import time
from datetime import datetime, timedelta

from dateutil.parser import parse
from steem.account import Account
from steem.post import Post
from steem.amount import Amount
from steem import Steem
import requests

def get_steem_conn(nodes):
    _steem_conn = Steem(
        nodes=nodes,
        # keys=[os.getenv("POSTING_KEY"), ]
    )

    return _steem_conn


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig()


class TagBot:

    def __init__(self, config, steemd_instance):
        self.config = config
        self.steemd_instance = steemd_instance
        self.target_tags = config.get("TAGS") or [config.get("TAG"), ]


    def fetch_tag(self, tag, start_date, end_date, start_author=None, start_permlink=None, posts=[], scanned_pages=0):
        while True:  
            logger.info("Fetching tag: #{} /p.{}".format(tag, scanned_pages+1) )
            query = {
                "limit": 100,
                "tag":tag
            }
            if start_author:
                query.update({
                    "start_author": start_author,
                    "start_permlink": start_permlink,
                })
            post_list = list(self.steemd_instance.get_discussions_by_created(query))
            for post in post_list:
                created_at = parse(post["created"])

                if created_at > end_date:
                    continue
                elif created_at < start_date:
                    return posts

                # try:
                #     if tag in json.loads(post["json_metadata"])["tags"]:
                #         logger.info('Post Found: {}'.format(post.get('title')))
                #         posts.append(post)
                # except Exception:
                #     pass

                posts.append(post)
            
            if not len(post_list):
                logger.info("No article Found with this tag")
                return posts

            # Prepare for next iteration
            scanned_pages += 1
            start_author=post["author"]
            start_permlink=post["permlink"]



    def start_making_report(self):
        '''
        @dev monthly report for specific tag
        '''
        start_date = datetime.strptime(self.config["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(self.config["end_date"], "%Y-%m-%d")
        logger.info('Parsing from {} to {}'.format(start_date, end_date))
        posts = []
        for tag in self.target_tags:
            posts += self.fetch_tag(tag, start_date, end_date)
        logger.info("%s posts found.", len(posts))

        report_file = open(self.config["output_name"].format(tag, self.config["start_date"], self.config["end_date"]),'w')
        report_file.write('Created, title, author, permlink,link\n')
        for post in posts:
            report_file.write('{},{},{},{},https://steemit.com/@{}/{}\n'.format(post.get("created"), post.get("title").replace(',',' ').replace('\n',' '), post.get("author"), post.get("permlink"),post.get("author"), post.get("permlink") ))
        logger.info('Report Written to {}'.format(self.config["output_name"]))


    def run(self):
        self.start_making_report()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Config file in JSON format")
    args = parser.parse_args()
    config = json.loads(open(args.config).read())
    upvote_bot = TagBot(
        config,
        get_steem_conn(config["NODES"])
    )
    upvote_bot.run()


if __name__ == '__main__':
    main()