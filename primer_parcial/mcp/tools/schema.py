"""
Tool: get_database_schema
Provides structured, safe information about the core database schema of Liga de Barrios y Fincas.
"""

from typing import Dict, Any, List
from sqlalchemy import text
from db import get_db_connection

# Allowed tables exposed to AI agents (avoids internal alembic tables and sensitive user tables)
ALLOWED_TABLES = [
    "tournaments",
    "teams",
    "players",
    "rounds",
    "pitches",
    "matches",
    "match_stats",
    "standings"
]

async def get_database_schema() -> Dict[str, Any]:
    """
    Devuelve información estructurada sobre las tablas principales de la base de datos,
    incluyendo columnas, tipos de datos, nulabilidad, claves primarias y relaciones de clave foránea.
    
    Esta herramienta es de solo lectura y excluye tablas y campos sensibles.
    """
    async with get_db_connection() as conn:
        # 1. Fetch columns for allowed tables
        cols_query = text("""
            SELECT 
                table_name,
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' 
              AND table_name = ANY(:tables)
            ORDER BY table_name, ordinal_position;
        """)
        cols_res = await conn.execute(cols_query, {"tables": ALLOWED_TABLES})
        cols_rows = cols_res.fetchall()

        # 2. Fetch primary keys
        pk_query = text("""
            SELECT 
                tc.table_name,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
              AND tc.table_schema = 'public'
              AND tc.table_name = ANY(:tables);
        """)
        pk_res = await conn.execute(pk_query, {"tables": ALLOWED_TABLES})
        pk_rows = pk_res.fetchall()
        pks_by_table: Dict[str, List[str]] = {}
        for row in pk_rows:
            pks_by_table.setdefault(row.table_name, []).append(row.column_name)

        # 3. Fetch foreign keys
        fk_query = text("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
             AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public'
              AND tc.table_name = ANY(:tables);
        """)
        fk_res = await conn.execute(fk_query, {"tables": ALLOWED_TABLES})
        fk_rows = fk_res.fetchall()
        fks_by_table: Dict[str, List[Dict[str, str]]] = {}
        for row in fk_rows:
            fks_by_table.setdefault(row.table_name, []).append({
                "column": row.column_name,
                "references_table": row.foreign_table_name,
                "references_column": row.foreign_column_name,
            })

        # Assemble schema
        tables_data = {}
        for row in cols_rows:
            t_name = row.table_name
            if t_name not in tables_data:
                tables_data[t_name] = {
                    "table_name": t_name,
                    "primary_key": pks_by_table.get(t_name, []),
                    "foreign_keys": fks_by_table.get(t_name, []),
                    "columns": []
                }
            tables_data[t_name]["columns"].append({
                "name": row.column_name,
                "type": row.data_type,
                "nullable": row.is_nullable == "YES",
                "default": row.column_default
            })

        return {
            "database": "liga_barrios",
            "exposed_tables_count": len(tables_data),
            "tables": tables_data,
            "description": "Esquema relacional del torneo Liga de Barrios y Fincas (PostgreSQL)."
        }
