"""
utils.py (Umbra-Discord-Bot)
:license: AGPL-3.0,see LICENSE for details

This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later.

Utilities for the Discord application.
Contains interactions with MariaDB and a custom config class. 
"""

from typing import List, Dict, Union, Optional
import mariadb


if __name__ == "__main__":
    raise RuntimeError("Ce module n'est pas destiné à être exécuté directement.")


class UmbraClientConfig:
    """
    This class contains all the stored configurations for the Discord application.
    
    Attributes
    ----------
    initial_extensions : List[str]
        An array of extensions to load from the extensions directory
    version : str
        The current version of the application
    source : str
        The source code of the application
    debug : bool
        Wether debug messages should be printed
    game : str
        The status message for the application
    dbname : str
        The database to use in MariaDB
    dbuser : str
        The user tu use in MariaDB
    dbpass : str
        The password to use in MariaDB
    dbhost : str
        The host to use in MariaDB
    dbport : int
        The port to use in MariaDB
    token : str
        The Discord token tu run the application, should be unset as soon as possible
    launch_time : int
        The POSIX timestamp of launch time
    temp_voice_list : List[int]
        The list of IDs of temporary voice channels
    voice_watch_list : List[int]
        The list of IDs of voice channels to watch for creating temporary voice channels
    here_allowed_channels : List[int]
        The list of IDs of channels where here command is allowed
    emoji_reacts : Dict[str, str]
        The dictionary of emojis and associated messages
    """
    def __init__(self, initial_extensions: List[str], config: dict):
        self.initial_extensions = initial_extensions
        self.version = "v1.5.1"
        self.source = "https://github.com/Captn138/Umbra-Discord-bot"
        self.debug = config.get("debug", "false") == "true"
        self.game = config.get("game", None)
        self.dbname = config.get("dbname", "umbra")
        self.dbuser = config.get("dbuser", "root")
        self.dbpass = config.get("dbpass", "")
        self.dbhost = config.get("dbhost", "127.0.0.1")
        self.dbport = int(config.get("dbport", "3306"))
        self.token = config.get("token", None)
        self.launch_time: int = None
        self.temp_voice_list: List[int] = []
        self.voice_watch_list: List[int] = []
        self.here_allowed_channels: List[int] = []
        self.emoji_reacts: Dict[str, str] = {}


class DbOperations:
    """
    This class contains static methods to interact with MariaDB.
    """
    @staticmethod
    def get_db(config: UmbraClientConfig):
        """
        Retrieves the connexion to MariaDB.
        
        Parameters
        ----------
        config : UmbraClientConfig
            The config object from which to load connexion parameters

        Returns
        -------
        mariadb.connections.Connection
            The connexion to MariaDB
        """
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

    @staticmethod
    def query_db(db: mariadb.connections.Connection, query: str, args: Optional[List[Union[str, int]]] = None, one: Optional[bool] = False):
        """
        Runs a query to MariaDB and returns the output.
        
        Parameters
        ----------
        db : mariadb.connections.Connection
            The connexion to MariaDB, retrieved from get_db()
        query : str
            The query to run, should not be an f-string, variables should be replaced by '?' and listed in order in args
        args : Optional[List[Union[str, int]]]
            An optional list containing all the variables that should be replaced in the query
        one : Optional[bool]
            Wether the query should only return the first result, defaults to False

        Returns
        -------
        Union[None, Dict[str, str], List[Dict[str, str]]]
            If Exception encountered, returns None
            If one = True, returns a dictionary with the first result
            Else, returns a list of dictionaries of all results
        """
        cur = db.cursor(dictionary=True)
        cur.execute(query, args)
        try:
            rv = cur.fetchall()
        except mariadb.Error:
            return None
        cur.close()
        return rv[0] if one else rv
