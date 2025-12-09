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

        # Table for Pulgarin products
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pulgarin_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT,
                descripcion TEXT NOT NULL,
                peso TEXT NOT NULL,
                um TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        ''')

        # Index for faster lookups by codigo
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pulgarin_codigo
            ON pulgarin_products(codigo)
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

    # Pulgarin Products Management Methods

    def save_product(self, codigo: Optional[str], descripcion: str,
                    peso: str, um: str) -> int:
        """Save or update a Pulgarin product

        Args:
            codigo: Product code (can be None)
            descripcion: Product description
            peso: Product weight
            um: Unit of measure (U/M)

        Returns:
            Product ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now()

        # Check if product exists (by codigo if provided, otherwise always insert)
        if codigo is not None:
            cursor.execute(
                'SELECT id FROM pulgarin_products WHERE codigo = ?',
                (codigo,)
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing product
                cursor.execute(
                    '''UPDATE pulgarin_products
                       SET descripcion = ?, peso = ?, um = ?, updated_at = ?
                       WHERE codigo = ?''',
                    (descripcion, peso, um, now, codigo)
                )
                product_id = existing[0]
            else:
                # Insert new product
                cursor.execute(
                    '''INSERT INTO pulgarin_products
                       (codigo, descripcion, peso, um, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (codigo, descripcion, peso, um, now, now)
                )
                product_id = cursor.lastrowid
        else:
            # Insert new product with NULL codigo
            cursor.execute(
                '''INSERT INTO pulgarin_products
                   (codigo, descripcion, peso, um, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (None, descripcion, peso, um, now, now)
            )
            product_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return product_id

    def get_product_by_code(self, codigo: str) -> Optional[dict]:
        """Get a product by its code

        Args:
            codigo: Product code

        Returns:
            Product dictionary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            '''SELECT id, codigo, descripcion, peso, um, created_at, updated_at
               FROM pulgarin_products
               WHERE codigo = ?''',
            (codigo,)
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_all_products(self, limit: Optional[int] = None,
                        offset: int = 0) -> list:
        """Get all Pulgarin products

        Args:
            limit: Maximum number of products to return (None for all)
            offset: Number of products to skip

        Returns:
            List of product dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if limit:
            cursor.execute(
                '''SELECT id, codigo, descripcion, peso, um, created_at, updated_at
                   FROM pulgarin_products
                   ORDER BY id DESC
                   LIMIT ? OFFSET ?''',
                (limit, offset)
            )
        else:
            cursor.execute(
                '''SELECT id, codigo, descripcion, peso, um, created_at, updated_at
                   FROM pulgarin_products
                   ORDER BY id DESC'''
            )

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def delete_product(self, product_id: Optional[int] = None,
                      codigo: Optional[str] = None) -> bool:
        """Delete a product by ID or codigo

        Args:
            product_id: Product ID
            codigo: Product code

        Returns:
            True if deleted, False if not found
        """
        if not product_id and not codigo:
            raise ValueError("Must provide either product_id or codigo")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if product_id:
            cursor.execute(
                'DELETE FROM pulgarin_products WHERE id = ?',
                (product_id,)
            )
        else:
            cursor.execute(
                'DELETE FROM pulgarin_products WHERE codigo = ?',
                (codigo,)
            )

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return deleted

    def get_products_count(self) -> int:
        """Get total count of Pulgarin products

        Returns:
            Total number of products
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM pulgarin_products')
        count = cursor.fetchone()[0]

        conn.close()
        return count
