# This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later

if __name__ == "__main__":
    raise RuntimeError("Ce module n'est pas destiné à être exécuté directement.")


import mariadb, traceback
from typing import List


class dbOperations:
    def get_db(config):
        if not hasattr(config, 'db') or config.db is None:
            config.db = mariadb.connect(
                        user = config.dbuser,
                        password = config.dbpass,
                        host = config.dbhost,
                        port = config.dbport,
                        database = config.dbname
            )
        config.db.auto_reconnect = True
        return config.db

    def query_db(db: mariadb.connections.Connection, query: str, args: List = [], one = False):
        try:
            cur = db.cursor(dictionary=True)
            cur.execute(query, args)
            try:
                rv = cur.fetchall()
            except:
                rv = None
            cur.close()
            return (rv[0] if rv else None) if one else rv
        except Exception:
            print(traceback.format_exc())