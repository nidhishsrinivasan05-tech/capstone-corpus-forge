import os
import sqlite3
from datetime import datetime

DB_PATH = "data/corpus_forge.db"


def get_connection():
    os.makedirs("data", exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    os.makedirs("data/uploads", exist_ok=True)
    with get_connection() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                filetype TEXT NOT NULL,
                path TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                kind TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_stats (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                request_count INTEGER NOT NULL,
                token_count INTEGER NOT NULL
            )
            """
        )
        db.execute(
            "INSERT OR IGNORE INTO usage_stats (id, request_count, token_count) VALUES (1, 0, 0)"
        )
        db.commit()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def add_usage(tokens):
    with get_connection() as db:
        db.execute(
            "UPDATE usage_stats SET request_count = request_count + 1, token_count = token_count + ? WHERE id = 1",
            (tokens,),
        )
        db.commit()
