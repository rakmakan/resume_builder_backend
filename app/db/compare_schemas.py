#!/usr/bin/env python3
from pathlib import Path
import sqlite3
from typing import Dict, List, Set

def get_table_schema(db_path: str) -> Dict[str, List[Dict]]:
    """Get schema information for all tables in a database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' 
    AND name NOT LIKE 'sqlite_%'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    # Get schema for each table
    schemas = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = []
        for col in cursor.fetchall():
            # col: (cid, name, type, notnull, dflt_value, pk)
            columns.append({
                'name': col[1],
                'type': col[2],
                'required': bool(col[3]),
                'default': col[4],
                'is_primary_key': bool(col[5])
            })
        schemas[table] = columns
    
    conn.close()
    return schemas

def print_schema_diff(frontend_schema: Dict[str, List[Dict]], 
                     backend_schema: Dict[str, List[Dict]]):
    """Print differences between frontend and backend schemas."""
    frontend_tables = set(frontend_schema.keys())
    backend_tables = set(backend_schema.keys())
    
    print("\nSchema Comparison Results:")
    print("=" * 50)
    
    # Check for tables that exist in frontend but not in backend
    missing_tables = frontend_tables - backend_tables
    if missing_tables:
        print("\nTables in frontend but missing in backend:")
        for table in sorted(missing_tables):
            print(f"- {table}")
            print("  Columns:")
            for col in frontend_schema[table]:
                print(f"    - {col['name']}: {col['type']}" + 
                      f" {'(Required)' if col['required'] else ''}" +
                      f" {'(PK)' if col['is_primary_key'] else ''}")
    
    # Check for extra tables in backend
    extra_tables = backend_tables - frontend_tables
    if extra_tables:
        print("\nExtra tables in backend (not in frontend):")
        for table in sorted(extra_tables):
            print(f"- {table}")
    
    # Compare schemas for common tables
    common_tables = frontend_tables & backend_tables
    schema_differences = False
    
    for table in sorted(common_tables):
        frontend_cols = {col['name']: col for col in frontend_schema[table]}
        backend_cols = {col['name']: col for col in backend_schema[table]}
        
        # Check for column differences
        if frontend_cols != backend_cols:
            if not schema_differences:
                print("\nSchema differences in common tables:")
                schema_differences = True
            
            print(f"\nTable: {table}")
            
            # Check for missing columns
            missing_cols = set(frontend_cols.keys()) - set(backend_cols.keys())
            if missing_cols:
                print("  Columns in frontend but missing in backend:")
                for col in missing_cols:
                    col_info = frontend_cols[col]
                    print(f"    - {col}: {col_info['type']}" +
                          f" {'(Required)' if col_info['required'] else ''}" +
                          f" {'(PK)' if col_info['is_primary_key'] else ''}")
            
            # Check for extra columns
            extra_cols = set(backend_cols.keys()) - set(frontend_cols.keys())
            if extra_cols:
                print("  Extra columns in backend:")
                for col in extra_cols:
                    col_info = backend_cols[col]
                    print(f"    - {col}: {col_info['type']}" +
                          f" {'(Required)' if col_info['required'] else ''}" +
                          f" {'(PK)' if col_info['is_primary_key'] else ''}")
            
            # Check for type differences in common columns
            common_cols = set(frontend_cols.keys()) & set(backend_cols.keys())
            for col in common_cols:
                if frontend_cols[col] != backend_cols[col]:
                    print(f"  Column {col} has differences:")
                    print(f"    Frontend: {frontend_cols[col]}")
                    print(f"    Backend:  {backend_cols[col]}")

def main():
    # Get database paths
    root_dir = Path(__file__).parent.parent
    frontend_db = root_dir / 'database' / 'resume.frontend.sqlite'
    backend_db = root_dir / 'database' / 'resume.sqlite'
    
    # Get schemas
    print(f"Analyzing frontend database: {frontend_db}")
    frontend_schema = get_table_schema(str(frontend_db))
    
    print(f"Analyzing backend database: {backend_db}")
    backend_schema = get_table_schema(str(backend_db))
    
    # Print differences
    print_schema_diff(frontend_schema, backend_schema)

if __name__ == "__main__":
    main()
