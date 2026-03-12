import os
import json
import logging
import sqlite3
import shutil

def setup_logging(log_file):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

class Database:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_table()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            channel TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def is_uploaded(self, filename):
        cursor = self.conn.execute("SELECT 1 FROM uploads WHERE filename = ?", (filename,))
        return cursor.fetchone() is not None

    def mark_as_uploaded(self, filename, channel):
        self.conn.execute("INSERT INTO uploads (filename, channel) VALUES (?, ?)", (filename, channel))
        self.conn.commit()

def move_to_archive(file_path, archive_dir):
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
    filename = os.path.basename(file_path)
    shutil.move(file_path, os.path.join(archive_dir, filename))
