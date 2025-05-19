# This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later

from typing import List, Dict, Union, Optional
import mariadb


if __name__ == "__main__":
    raise RuntimeError("Ce module n'est pas destiné à être exécuté directement.")


class UmbraClientConfig:
    def __init__(self, initial_extensions: List[str], config: dict):
        self.initial_extensions = initial_extensions
        self.dbname = config.get("dbname", "umbra")
        self.dbuser = config.get("dbuser", "root")
        self.dbpass = config.get("dbpass", "")
        self.dbhost = config.get("dbhost", "127.0.0.1")
        self.dbport = int(config.get("dbport", "3306"))
        self.token = config.get("token", None)
        self.temp_voice_list: List[int] = []
        self.voice_watch_list: List[int] = []
        self.here_allowed_channels: List[int] = []
        self.emoji_reacts: Dict[str, str] = {}


class DbOperations:
    def get_db(config: UmbraClientConfig):
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

    def query_db(db: mariadb.connections.Connection, query: str, args: Optional[List[Union[str, int]]] = None, one = False):
        cur = db.cursor(dictionary=True)
        cur.execute(query, args)
        try:
            rv = cur.fetchall()
        except mariadb.Error:
            return None
        cur.close()
        return rv[0] if one else rv
