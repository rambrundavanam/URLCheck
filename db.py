import psycopg2
import sys
import logging


class DB:
    def db_connect(self):
        try:
            client = psycopg2.connect(user="postgres",
                                      password="4y7sV96vA9wv46VR",
                                      host="127.0.0.1",
                                      port="5432",
                                      database="urls")
            cursor = client.cursor()
            self.dump_urls_to_db(cursor, client)
            client.close()
            if cursor is True:
                return client
        except Exception as e:
            print("Authentication Error {}".format(e))
            sys.exit(1)

    def dump_urls_to_db(self, cursor, client):
        try:
            with open("urls.txt", "rb") as fd:
                lines = fd.readlines()
                for line in lines:
                    decision = ""
                    reason = "Test data for Reason, try with a new url in format"
                    line = line.decode("utf-8").strip()
                    if "good" in line or "safe" in line:
                        decision = 'SAFE'
                    else:
                        decision = 'NOTSAFE'
                    hostname, query = line.split("/")
                    hostname, port = hostname.split(":")
                    postgres_insert_query = """ INSERT INTO urls(KEY, HOSTNAME, PORT, QUERY, DECISION, REASON) VALUES (%s,%s,%s, %s, %s, %s)"""
                    record_to_insert = (line, hostname, int(port), query, decision, reason)
                    logging.info("Adding lines to DB")
                    cursor.execute(postgres_insert_query, record_to_insert)
                    client.commit()
                fd.close()
        except Exception as error:
            print("Error:{}".format(error))


if __name__ == '__main__':
    db = DB()
    cursor = db.db_connect()
