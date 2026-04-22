import sqlite3

DB_PATH = "rag.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS chunks")
    cur.execute("""
    CREATE TABLE chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patch_version TEXT,
        patch_title TEXT,
        category TEXT,
        entity_name TEXT,
        title TEXT,
        content TEXT,
        url TEXT,
        image_urls TEXT,
        order_index INTEGER
    )
    """)
    conn.commit()
    conn.close()
