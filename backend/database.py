"""
database.py
-----------
Handles the SQLite connection and table creation for the Mayom Holdings
admin panel (mayom.db).

Run this file directly once to create/reset the database:
    python database.py
"""

import sqlite3
import os

# mayom.db will be created in the same folder as this file
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mayom.db")


def get_db_connection():
    """Return a sqlite3 connection with rows accessible by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't already exist."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Admin users who can log in to the dashboard
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            email         TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL DEFAULT (datetime('now')),
            last_login    TEXT
        )
    """)

    # Enquiries submitted through the website's "Send enquiry" form
    cur.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name     TEXT NOT NULL,
            organisation  TEXT,
            email         TEXT NOT NULL,
            interest      TEXT,
            message       TEXT,
            status        TEXT NOT NULL DEFAULT 'new',   -- new / contacted / closed
            created_at    TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    print(f"Database ready at: {DB_PATH}")


if __name__ == "__main__":
    init_db()