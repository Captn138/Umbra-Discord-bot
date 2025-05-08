import sqlite3, traceback


class dbOperations:
    def get_db(name):
        db = sqlite3.connect(name)
        db.row_factory = sqlite3.Row
        return db

    def query_db(db, query, args=(), one=False):
        try:
            cur = db.execute(query, args)
            if query.strip().lower().startswith(("insert", "update", "delete", "replace")):
                db.commit()
            rv = cur.fetchall()
            cur.close()
            return (rv[0] if rv else None) if one else rv
        except Exception:
            print(traceback.format_exc())