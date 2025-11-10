import sqlite3

db_path="test.db"

conn=sqlite3.connect(db_path)

with conn:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
    );
    """)

conn.close()