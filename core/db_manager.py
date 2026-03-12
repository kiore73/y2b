import sqlite3
import os
import logging

class DBManager:
    def __init__(self, db_path="data/bot_database.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT,
                    title TEXT,
                    description TEXT,
                    channel_name TEXT,
                    status TEXT DEFAULT 'pending', 
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS upload_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT,
                    channel_name TEXT,
                    title TEXT,
                    status TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def add_to_queue(self, file_path, title, description, channel_name):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO video_queue (file_path, title, description, channel_name)
                VALUES (?, ?, ?, ?)
            """, (file_path, title, description, channel_name))
            conn.commit()
            return cursor.lastrowid

    def get_next_for_channel(self, channel_name):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM video_queue 
                WHERE channel_name = ? AND status = 'pending' 
                ORDER BY created_at ASC LIMIT 1
            """) # Ошибка была тут: пропущен параметр
            # Исправляю сразу
            cursor.execute("""
                SELECT * FROM video_queue 
                WHERE channel_name = ? AND status = 'pending' 
                ORDER BY created_at ASC LIMIT 1
            """, (channel_name,))
            return cursor.fetchone()

    def update_status(self, video_id, status, error_message=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE video_queue 
                SET status = ?, error_message = ? 
                WHERE id = ?
            """, (status, error_message, video_id))
            conn.commit()

    def get_queue_stats(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT channel_name, COUNT(*) 
                FROM video_queue 
                WHERE status = 'pending' 
                GROUP BY channel_name
            """)
            return dict(cursor.fetchall())

    def get_full_queue(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, channel_name, status FROM video_queue 
                WHERE status = 'pending' ORDER BY created_at ASC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def clear_queue(self, channel_name=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if channel_name:
                cursor.execute("DELETE FROM video_queue WHERE channel_name = ? AND status = 'pending'", (channel_name,))
            else:
                cursor.execute("DELETE FROM video_queue WHERE status = 'pending'")
            conn.commit()
            return cursor.rowcount
