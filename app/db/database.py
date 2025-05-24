from pathlib import Path
from typing import Dict, List, Optional, Any
import sqlite3
from pydantic import create_model, BaseModel

class DatabaseInspector:
    def __init__(self, db_path: str):
        """Initialize database inspector with path to SQLite database."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        """Create database connection."""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def get_all_tables(self) -> List[str]:
        """Get list of all tables in the database."""
        self.connect()
        query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        AND name NOT LIKE 'sqlite_%'
        """
        self.cursor.execute(query)
        tables = [row[0] for row in self.cursor.fetchall()]
        return tables

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema information for a specific table."""
        self.connect()
        query = f"PRAGMA table_info({table_name})"
        self.cursor.execute(query)
        columns = []
        for col in self.cursor.fetchall():
            # col: (cid, name, type, notnull, dflt_value, pk)
            columns.append({
                'name': col[1],
                'type': col[2],
                'required': bool(col[3]),
                'default': col[4],
                'is_primary_key': bool(col[5])
            })
        return columns

    def create_pydantic_model(self, table_name: str) -> type:
        """Create a Pydantic model from table schema."""
        columns = self.get_table_schema(table_name)
        fields = {}
        
        type_mapping = {
            'INTEGER': int,
            'TEXT': str,
            'TIMESTAMP': str,  # You might want to use datetime here
            'REAL': float,
            'NUMERIC': float,
            'BOOLEAN': bool
        }

        for col in columns:
            # Skip auto-increment primary key fields
            if col['is_primary_key'] and col['type'].upper() == 'INTEGER':
                continue

            field_type = type_mapping.get(col['type'].upper(), str)
            
            # Make field optional if it's nullable or has a default value
            if not col['required'] or col['default'] is not None:
                field_type = Optional[field_type]

            fields[col['name']] = (field_type, None)

        model_name = f"{table_name.title().replace('_', '')}Model"
        return create_model(model_name, **fields, __base__=BaseModel)

    def get_all_models(self) -> Dict[str, type]:
        """Create Pydantic models for all tables in the database."""
        tables = self.get_all_tables()
        return {table: self.create_pydantic_model(table) for table in tables}
