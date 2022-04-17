import threading

import loguru
from couchdb import Unauthorized

from common_util.config_handler import ConfigHandler
import couchdb

from loguru import logger

from nlp_util.sentiment_helper import SentimentHelper
from twitter_util import twitter_preprocess_helper


class DbHelper:
    # singleton
    __instance = None

    # singleton
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(DbHelper, cls).__new__(
                cls, *args, **kwargs)

            # init
            self = cls.__instance

            self.__index = 0

            self.__config_handler = ConfigHandler()

            # init db connections
            db_username = self.__config_handler.get_db_username()
            db_password = self.__config_handler.get_db_password()

            db_host_port_list = self.__config_handler.get_db_host_port_list()
            host_list_size = len(db_host_port_list)

            # database connection pool
            self.__db_connections = []
            for i in range(0, host_list_size):
                url = 'http://' + db_username + ':' + db_password + '@' + db_host_port_list[i]
                db_connection = couchdb.Server(url)
                logger.debug('db url is: ' + url)
                self.__db_connections.append(db_connection)

            logger.debug("db server list: " + str(self.__db_connections))

            # for RR load balance
            self.__db_connections_size = len(self.__db_connections)
            self.__db_connection_index = 0
            self.lock = threading.RLock()

        return cls.__instance

    # once we used __new__, __init__ is not needed
    def __init__(self):
        pass

    def __pick_db_via_rr_load_balance(self):
        """
        Round Robin to get a valid database connection

        :return: A valid database connnection instance

        author: xiaotian li
        """
        self.lock.acquire()
        try:
            if self.__db_connection_index < self.__db_connections_size:
                # Pick one server from host-list
                server = self.__db_connections[self.__db_connection_index]

                # prevent over bound
                if self.__db_connection_index < self.__db_connections_size - 1:
                    self.__db_connection_index += 1
                else:
                    self.__db_connection_index = 0

                db_name = self.__config_handler.get_target_db_name()
                try:
                    logger.debug('picked db name: ' + db_name + ' from: ' + str(server))
                    # try connect to this database
                    return server[db_name]

                except ConnectionRefusedError:
                    logger.error('db connection failed! on ' + str(server))
                    return None

                except Unauthorized:
                    logger.error('db password/username incorrect!')
                    return None

                except OSError as e:
                    logger.error(e)
                    return None

                except Exception as e:

                    logger.debug('db: ' + db_name + ' not exist, created.')
                    return server.create(db_name)
            else:
                logger.error("host list out of bound at get_current_db_host")
                exit(-1)
        finally:
            self.lock.release()

    def put_twitter_to_db(self, tweet_doc):
        """
        put the tweet doc into the database

        :param tweet_doc: fetched from tw api
        author: xiaotian li
        """
        if tweet_doc is None:
            return

        database = None
        # pickup one database with RoundRobin load balance to put tweet
        for i in range(0, self.__db_connections_size):
            database = self.__pick_db_via_rr_load_balance()

            # if we can connect to this database
            if database is not None:
                break

        # if the db is still none
        if database is None:

            logger.error('all database nodes are dead!!')
            exit(-1)

        # prevent duplicate twitter
        if str(tweet_doc["id"]) not in database:
            # preprocess original tweet_doc, then store it in db
            twitter_dict = twitter_preprocess_helper.preprocess_twitter(tweet_doc)

            try:
                database.save(twitter_dict)
            except Exception as e:
                logger.error(e)



if __name__ == '__main__':
    a = DbHelper()

    a.put_twitter_to_db(None)
    a.put_twitter_to_db(None)
    a.put_twitter_to_db(None)
    a.put_twitter_to_db(None)
    a.put_twitter_to_db(None)

