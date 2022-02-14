import redis
import sys
import psycopg2
import enum
from flask import Flask, jsonify
from flask_caching import Cache
from psycopg2 import pool
from ReturnTypes import *

app = Flask(__name__)
app.config.from_object('config.Config')  # Set the configuration variables to the flask application
cache = Cache(app)  # Initialize Cache

# Thread pool creates a pool of connections and assings a connection when requested
connection_pool = psycopg2.pool.ThreadedConnectionPool(5, 20, user="postgres",
                                                       password="4y7sV96vA9wv46VR",
                                                       host="host.docker.internal",
                                                       port="5432",
                                                       database="urls")  # host has to be this on a mac


def postgres_connect():
    """
    Requests a postgres connection from pool
    :return:
    """
    try:
        conn = connection_pool.getconn()
        if conn:
            app.logger.info("Connection returned  successfully from pool")
        return conn
    except Exception as e:
        app.logger.error("Connection Error in Postgres {}".format(e))
        sys.exit(1)


def redis_connect() -> redis.client.Redis:
    """
    Creates a connection redis cache
    :return: connection object
    """
    try:
        client = redis.Redis(host="redis",
                             port=6379,
                             db=0,
                             socket_timeout=5,
                             decode_responses=True)
        ping = client.ping()
        if ping is True:
            return client
    except redis.AuthenticationError:
        app.logger.info("Authentication Error")
        sys.exit(1)


def create_postgres_tables():
    """
    Creates a table in the postgres db for storing data
    :return:
    """
    try:
        connection = postgres_connect()
        cursor = connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS urls")
        sql = '''CREATE TABLE urls(
                KEY TEXT PRIMARY KEY NOT NULL,
                HOSTNAME TEXT NOT NULL,
                PORT INT NOT NULL,
                QUERY TEXT NOT NULL,
                DECISION TEXT NOT NULL,
                REASON TEXT NOT NULL)'''
        cursor.execute(sql)
        app.logger.info("Successfully create urls table")
        connection.commit()
        cursor.close()
        connection_pool.putconn(connection)
    except Exception as error:
        app.logger.error("Exception in creating the table {}".format(error))


create_postgres_tables()
redisclient = redis_connect()


def set_route_to_database(url: str, hostname: str, port: int, query: str, decision: str, reason: str) -> bool:
    """
    Sets data into the postgres db table
    :param url:
    :param hostname:
    :param port:
    :param query:
    :param decision:
    :return:
    """
    try:
        app.logger.info("Setting Data to Postgres DB")
        connection = postgres_connect()
        cursor = connection.cursor()
        sql_query = """INSERT INTO urls(KEY, HOSTNAME, PORT, QUERY, DECISION, REASON) VALUES (%s,%s,%s, %s, %s, %s)"""
        record_to_insert = (url, hostname, int(port), query, decision, reason)
        cursor.execute(sql_query, record_to_insert)
        connection.commit()
        connection_pool.putconn(connection)
        return True
    except Exception as error:
        app.logger.error("Exception in Inserting data into PostGres {}".format(error))


def get_routes_from_database(url: str) -> dict:
    """
    Gets data from postgres database for a key
    :param url:
    :return:
    """
    try:
        app.logger.info("Getting Data from Postgres DB")
        connection = postgres_connect()
        cursor = connection.cursor()
        query = "SELECT * FROM urls WHERE KEY=%s"
        cursor.execute(query, (url,))
        response = cursor.fetchall()  # fetch result of the query from db
        cursor.close()
        connection_pool.putconn(connection)
        return response
    except Exception as error:
        app.logger.error("Exception in getting Data from PostGres {}".format(error))


def get_routes_from_cache(key: str):
    """
    Gets data from redis cache for a KEY/URL
    :param key:
    :return: data
    """
    try:
        app.logger.info("Getting Data from Redis Cache")
        data = redisclient.hgetall(key)  # get the whole info for that key
        return data
    except Exception as error:
        app.logger.error("Exception in getting Data from REDIS {}".format(error))


def safe_check(hostname, query):
    """
    Main function that does cache - db check, calls functions to set data into db and cache
    :param hostname:
    :param query:
    :return: result in json format from cache or db
    """
    url = hostname + "/" + query
    cache_redis = get_routes_from_cache(url)  # get url from cache
    try:
        if cache_redis:
            return cache_redis
        else:
            db = get_routes_from_database(url)  # get url from db
            hostname, port = hostname.split(":")
            decision = Returns.SAFE.name
            reason = Reasons.DEFAULT.value
            if not db:
                if len(query) > 100:
                    reason = Reasons.LENGTH.value
                    decision = Returns.NOTSAFE.name
                elif int(port) in range(20000, 24000):
                    reason = Reasons.PORT.value
                    decision = Returns.NOTSAFE.name
                elif (NotSafe.MALICIOUS.name.casefold() in hostname.casefold() or
                      NotSafe.HARMFUL.name.casefold() in hostname.casefold() or
                      NotSafe.DANGEROUS.name.casefold() in hostname.casefold()):
                    reason = Reasons.HOSTNAME.value
                    decision = Returns.NOTSAFE.name
                else:
                    app.logger.info("URL seems legit")
                set_route_to_database(url, hostname, port, query, decision, reason)  #set data to db, it is a new record
                redisclient.hset(url, URLResponse.HOSTNAME.name, hostname)  # set this data into Redis cache
                redisclient.hset(url, URLResponse.PORT.name, port)
                redisclient.hset(url, URLResponse.QUERY.name, query)
                redisclient.hset(url, URLResponse.DECISION.name, decision)
                redisclient.hset(url, URLResponse.REASON.name, reason)
            return jsonify({URLResponse.HOSTNAME.name: hostname, URLResponse.PORT.name: port,
                            URLResponse.QUERY.name: query, URLResponse.DECISION.name: decision,
                            URLResponse.REASON.name: reason})

    except Exception as error:
        app.logger.error("Exception in getting from safe check {}".format(error))


@app.get('/urlinfo/1/<string:hostname>/<string:query>')  # url hits this first which is exposed
@cache.cached(timeout=600)
def check(hostname: str, query: str):
    """
    Takes a url in the required format, returns the response to use after processing
    :param hostname:
    :param query:
    :return:
    """
    return safe_check(hostname, query)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
