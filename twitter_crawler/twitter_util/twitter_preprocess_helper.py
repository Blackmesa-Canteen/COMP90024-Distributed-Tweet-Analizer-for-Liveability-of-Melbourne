from loguru import logger

from common_util import config_handler
from common_util.config_handler import ConfigHandler
from nlp_util.sentiment_helper import SentimentHelper

CONFIG = ConfigHandler()


def preprocess_twitter(original_twitter_doc):
    """
    preprocess the original twitter fetched to object that is suitable for database to store

    :param original_twitter_doc: original twitter json doc
    :return: twitter_dict: the dict that is suitable for database to store
    {
        '_id': '493805281185263600',
        'id': '493805281185263600',
        'created_at': 'Mon Jul 28 17:08:48 +0000 2014',
        'text': 'What? Boiled Milk? You mean.... Burnt milk. *facepalm*',
        'iso_language_code': 'en',
        'lang': 'en',
        'coordinates': {
            'type': 'Point',
            'coordinates': [Decimal('145.2093684'), Decimal('-37.8145959')]
        },
        'purified_text': 'boil silk mean ... burnt milk facepalm',
        'polarity': -0.3125,
        'subjectivity': 0.6875
    }

    author: xiaotian li
    """

    tweet_dict = dict()

    # set tweet id as document id
    if original_twitter_doc.get('id') is not None:
        tweet_dict["_id"] = str(original_twitter_doc["id"])

    else:
        tweet_dict["_id"] = str(original_twitter_doc["_id"])
    tweet_dict["id"] = tweet_dict["_id"]

    # date: created_at : "Wed Jan 01 00:00:00 +0000 2020"
    tweet_dict["created_at"] = original_twitter_doc['created_at']

    # unify text attribute
    if "full_text" in original_twitter_doc:
        tweet_dict["text"] = original_twitter_doc["full_text"]
    else:
        tweet_dict["text"] = original_twitter_doc["text"]

    # get the full text
    if original_twitter_doc.get("truncated") is not None and original_twitter_doc["truncated"]:
        tweet_dict["text"] = original_twitter_doc["extended_tweet"]["full_text"]

    # get language info
    if original_twitter_doc.get("metadata") is not None and \
            original_twitter_doc["metadata"].get("iso_language_code") is not None:

        tweet_dict["iso_language_code"] = original_twitter_doc["metadata"]["iso_language_code"]
    else:
        tweet_dict["iso_language_code"] = "und"

    if original_twitter_doc.get("lang") is not None:
        tweet_dict["lang"] = original_twitter_doc["lang"]
    else:
        tweet_dict["lang"] = "und"

    # get coordinates
    if original_twitter_doc.get("coordinates") is not None:
        tweet_dict["coordinates"] = original_twitter_doc["coordinates"]
    else:
        # default coordinates
        tweet_dict["coordinates"] = {
            'type': 'Point',
            'coordinates': [144.9631, 37.8136]
        }

    # Do NLP process
    npl_helper = SentimentHelper()

    # only do NLP on english twitter
    if CONFIG.is_fetch_english_tweet_only():
        tweet_dict["purified_text"] = npl_helper.get_sanitized_text(tweet_dict["text"])
        tweet_dict["polarity"] = npl_helper.get_polarity_from_text(tweet_dict["purified_text"])
        tweet_dict["subjectivity"] = npl_helper.get_subjectivity_from_text(tweet_dict["purified_text"])
    else:
        tweet_dict["purified_text"] = ""
        tweet_dict["polarity"] = 0.0
        tweet_dict["subjectivity"] = 0.0

    # tweet_dict["place"] = original_twitter_doc["place"]

    return tweet_dict
