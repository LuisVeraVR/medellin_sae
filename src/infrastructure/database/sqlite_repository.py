"""SQLite Database Repository Implementation - Infrastructure Layer"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from src.domain.repositories.database_repository import DatabaseRepository


class SQLiteRepository(DatabaseRepository):
    """SQLite implementation of database repository"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table for processed emails
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_emails (
                email_id TEXT PRIMARY KEY,
                processed_at TIMESTAMP NOT NULL
            )
        ''')

        # Table for processed invoices
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT NOT NULL,
                email_id TEXT NOT NULL,
                processed_at TIMESTAMP NOT NULL,
                csv_file TEXT NOT NULL,
                FOREIGN KEY (email_id) REFERENCES processed_emails(email_id)
            )
        ''')

        # Table for processing logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL
            )
        ''')

        conn.commit()
        conn.close()

    def is_email_processed(self, email_id: str) -> bool:
        """Check if email has been processed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT COUNT(*) FROM processed_emails WHERE email_id = ?',
            (email_id,)
        )

        count = cursor.fetchone()[0]
        conn.close()

        return count > 0

    def mark_email_processed(self, email_id: str, timestamp: datetime) -> None:
        """Mark email as processed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'INSERT OR IGNORE INTO processed_emails (email_id, processed_at) VALUES (?, ?)',
            (email_id, timestamp)
        )

        conn.commit()
        conn.close()

    def save_invoice_record(self, invoice_number: str, email_id: str,
                           timestamp: datetime, csv_file: str) -> None:
        """Save invoice processing record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            '''INSERT INTO processed_invoices
               (invoice_number, email_id, processed_at, csv_file)
               VALUES (?, ?, ?, ?)''',
            (invoice_number, email_id, timestamp, csv_file)
        )

        conn.commit()
        conn.close()

    def log_processing(self, level: str, message: str, timestamp: datetime) -> None:
        """Log processing event to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'INSERT INTO processing_logs (timestamp, level, message) VALUES (?, ?, ?)',
            (timestamp, level, message)
        )

        conn.commit()
        conn.close()

    def get_processing_stats(self) -> dict:
        """Get processing statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Count processed emails
        cursor.execute('SELECT COUNT(*) FROM processed_emails')
        emails_count = cursor.fetchone()[0]

        # Count processed invoices
        cursor.execute('SELECT COUNT(*) FROM processed_invoices')
        invoices_count = cursor.fetchone()[0]

        # Count errors
        cursor.execute('SELECT COUNT(*) FROM processing_logs WHERE level = ?', ('ERROR',))
        errors_count = cursor.fetchone()[0]

        conn.close()

        return {
            'emails_processed': emails_count,
            'invoices_generated': invoices_count,
            'errors': errors_count
        }
