"""Somex SQLite Database Repository - Infrastructure Layer"""
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


class SomexRepository:
    """SQLite repository for Somex processing data"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema for Somex"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table for Somex items (for comparison and reference)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS somex_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_item TEXT NOT NULL,
                referencia TEXT,
                descripcion TEXT,
                id_plan TEXT,
                desc_plan TEXT,
                id_mayor TEXT,
                descripcion_plan TEXT,
                row_id_item TEXT,
                categoria TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                UNIQUE(codigo_item, referencia)
            )
        ''')

        # Table for processed XML files (to avoid reprocessing)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS somex_processed_xml (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                xml_hash TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                zip_filename TEXT,
                processed_at TIMESTAMP NOT NULL,
                invoice_number TEXT,
                excel_file TEXT
            )
        ''')

        # Table for Somex processing logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS somex_processing_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                xml_filename TEXT
            )
        ''')

        # Create indexes for better performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_xml_hash
            ON somex_processed_xml(xml_hash)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_item_codigo
            ON somex_items(codigo_item)
        ''')

        conn.commit()
        conn.close()

    def get_xml_hash(self, xml_content: bytes) -> str:
        """Generate SHA256 hash of XML content"""
        return hashlib.sha256(xml_content).hexdigest()

    def is_xml_processed(self, xml_content: bytes) -> bool:
        """Check if XML has been processed based on content hash"""
        xml_hash = self.get_xml_hash(xml_content)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT COUNT(*) FROM somex_processed_xml WHERE xml_hash = ?',
            (xml_hash,)
        )

        count = cursor.fetchone()[0]
        conn.close()

        return count > 0

    def mark_xml_processed(
        self,
        xml_content: bytes,
        filename: str,
        zip_filename: Optional[str] = None,
        invoice_number: Optional[str] = None,
        excel_file: Optional[str] = None
    ) -> None:
        """Mark XML as processed"""
        xml_hash = self.get_xml_hash(xml_content)
        timestamp = datetime.now()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            '''INSERT OR IGNORE INTO somex_processed_xml
               (xml_hash, filename, zip_filename, processed_at, invoice_number, excel_file)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (xml_hash, filename, zip_filename, timestamp, invoice_number, excel_file)
        )

        conn.commit()
        conn.close()

    def save_item(self, item_data: Dict[str, Any]) -> None:
        """Save or update item information"""
        timestamp = datetime.now()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            '''INSERT INTO somex_items
               (codigo_item, referencia, descripcion, id_plan, desc_plan,
                id_mayor, descripcion_plan, row_id_item, categoria,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(codigo_item, referencia) DO UPDATE SET
                   descripcion = excluded.descripcion,
                   id_plan = excluded.id_plan,
                   desc_plan = excluded.desc_plan,
                   id_mayor = excluded.id_mayor,
                   descripcion_plan = excluded.descripcion_plan,
                   row_id_item = excluded.row_id_item,
                   categoria = excluded.categoria,
                   updated_at = excluded.updated_at''',
            (
                item_data.get('codigo_item', ''),
                item_data.get('referencia', ''),
                item_data.get('descripcion', ''),
                item_data.get('id_plan', ''),
                item_data.get('desc_plan', ''),
                item_data.get('id_mayor', ''),
                item_data.get('descripcion_plan', ''),
                item_data.get('row_id_item', ''),
                item_data.get('categoria', ''),
                timestamp,
                timestamp
            )
        )

        conn.commit()
        conn.close()

    def save_items_bulk(self, items: List[Dict[str, Any]]) -> int:
        """Save multiple items in bulk"""
        timestamp = datetime.now()
        count = 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for item_data in items:
            cursor.execute(
                '''INSERT INTO somex_items
                   (codigo_item, referencia, descripcion, id_plan, desc_plan,
                    id_mayor, descripcion_plan, row_id_item, categoria,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(codigo_item, referencia) DO UPDATE SET
                       descripcion = excluded.descripcion,
                       id_plan = excluded.id_plan,
                       desc_plan = excluded.desc_plan,
                       id_mayor = excluded.id_mayor,
                       descripcion_plan = excluded.descripcion_plan,
                       row_id_item = excluded.row_id_item,
                       categoria = excluded.categoria,
                       updated_at = excluded.updated_at''',
                (
                    item_data.get('codigo_item', ''),
                    item_data.get('referencia', ''),
                    item_data.get('descripcion', ''),
                    item_data.get('id_plan', ''),
                    item_data.get('desc_plan', ''),
                    item_data.get('id_mayor', ''),
                    item_data.get('descripcion_plan', ''),
                    item_data.get('row_id_item', ''),
                    item_data.get('categoria', ''),
                    timestamp,
                    timestamp
                )
            )
            count += 1

        conn.commit()
        conn.close()

        return count

    def clear_all_items(self) -> None:
        """Clear all items from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM somex_items')

        conn.commit()
        conn.close()

    def get_item_by_code(self, codigo_item: str) -> Optional[Dict[str, Any]]:
        """Get item information by code"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM somex_items WHERE codigo_item = ?',
            (codigo_item,)
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_item_by_description(self, descripcion: str) -> Optional[Dict[str, Any]]:
        """
        Get item information by description (partial match)

        Args:
            descripcion: Product description/name to search for

        Returns:
            Item data or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Try exact match first
        cursor.execute(
            'SELECT * FROM somex_items WHERE descripcion = ?',
            (descripcion,)
        )

        row = cursor.fetchone()

        # If no exact match, try partial match
        if not row:
            cursor.execute(
                'SELECT * FROM somex_items WHERE descripcion LIKE ?',
                (f'%{descripcion}%',)
            )
            row = cursor.fetchone()

        conn.close()

        if row:
            return dict(row)
        return None

    def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all items"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM somex_items ORDER BY codigo_item')

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def log_processing(
        self,
        level: str,
        message: str,
        xml_filename: Optional[str] = None
    ) -> None:
        """Log processing event"""
        timestamp = datetime.now()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            '''INSERT INTO somex_processing_logs
               (timestamp, level, message, xml_filename)
               VALUES (?, ?, ?, ?)''',
            (timestamp, level, message, xml_filename)
        )

        conn.commit()
        conn.close()

    def get_processing_stats(self) -> Dict[str, int]:
        """Get processing statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Count processed XMLs
        cursor.execute('SELECT COUNT(*) FROM somex_processed_xml')
        xml_count = cursor.fetchone()[0]

        # Count items
        cursor.execute('SELECT COUNT(*) FROM somex_items')
        items_count = cursor.fetchone()[0]

        # Count errors
        cursor.execute(
            'SELECT COUNT(*) FROM somex_processing_logs WHERE level = ?',
            ('ERROR',)
        )
        errors_count = cursor.fetchone()[0]

        conn.close()

        return {
            'xml_processed': xml_count,
            'items_count': items_count,
            'errors': errors_count
        }

    def get_processed_xml_list(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of processed XMLs"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            '''SELECT * FROM somex_processed_xml
               ORDER BY processed_at DESC
               LIMIT ?''',
            (limit,)
        )

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
