# This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later

if __name__ == "__main__":
    raise RuntimeError("Ce module n'est pas destiné à être exécuté directement.")


import sqlite3, traceback
from typing import List


class dbOperations:
    def get_db(name: str):
        db = sqlite3.connect(name)
        db.row_factory = sqlite3.Row
        return db

    def query_db(db: sqlite3.Connection, query: str, args: List = [], one = False):
        try:
            cur = db.execute(query, args)
            if query.strip().lower().startswith(("insert", "update", "delete", "replace")):
                db.commit()
            rv = cur.fetchall()
            cur.close()
            return (rv[0] if rv else None) if one else rv
        except Exception:
            print(traceback.format_exc())