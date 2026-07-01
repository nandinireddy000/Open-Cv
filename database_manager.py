import sqlite3
import datetime
import os

class DatabaseManager:
    def __init__(self, db_path='parking_data.db'):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        if not os.path.exists(self.db_path):
            with self.get_connection() as conn:
                with open('schema.sql', 'r') as f:
                    conn.executescript(f.read())
                conn.commit()
        else:
            # Ensure tables exist even if file exists
            with self.get_connection() as conn:
                with open('schema.sql', 'r') as f:
                    conn.executescript(f.read())
                conn.commit()

    def update_slot_status(self, slot_id, status):
        """Updates current status and logs change if status changed."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check previous status
            cursor.execute("SELECT status FROM current_status WHERE slot_id = ?", (slot_id,))
            row = cursor.fetchone()
            
            if row is None or row['status'] != status:
                # Update current status (upsert)
                cursor.execute("""
                    INSERT INTO current_status (slot_id, status, last_updated) 
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(slot_id) DO UPDATE SET 
                    status=excluded.status, 
                    last_updated=CURRENT_TIMESTAMP
                """, (slot_id, status))
                
                # Log history
                cursor.execute("INSERT INTO parking_logs (slot_id, status) VALUES (?, ?)", (slot_id, status))
                conn.commit()

    def get_all_slots(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM current_status ORDER BY slot_id")
            return [dict(row) for row in cursor.fetchall()]

    def get_history(self, limit=50):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM parking_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]
