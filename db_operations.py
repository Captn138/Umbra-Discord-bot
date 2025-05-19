# This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later

from typing import List, Dict
import mariadb


if __name__ == "__main__":
    raise RuntimeError("Ce module n'est pas destiné à être exécuté directement.")


class DbOperations:
    def get_db(config: Dict[str, str]):
        if not hasattr(config, "db") or config.db is None:  # pylint: disable=E0203
            config.db = mariadb.connect(    # pylint: disable=W0201
                        user = config.dbuser,
                        password = config.dbpass,
                        host = config.dbhost,
                        port = config.dbport,
                        database = config.dbname
            )
        config.db.auto_reconnect = True
        config.db.autocommit = True
        return config.db

    def query_db(db: mariadb.connections.Connection, query: str, args: List = None, one = False):
        cur = db.cursor(dictionary=True)
        cur.execute(query, args)
        try:
            rv = cur.fetchall()
        except mariadb.Error:
            return None
        cur.close()
        return rv[0] if one else rv
