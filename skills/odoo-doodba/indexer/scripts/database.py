"""SQLite database operations and schema management."""

import sqlite3
import aiosqlite
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Optional
from contextlib import contextmanager, asynccontextmanager

logger = logging.getLogger(__name__)


def sanitize_db_param(value):
    """Convert list/dict parameters to JSON strings for SQLite compatibility.

    SQLite doesn't support Python list/dict types directly. This function
    serializes complex types to JSON strings while keeping strings/None as-is.

    Args:
        value: Parameter value to sanitize

    Returns:
        Sanitized value suitable for SQLite binding
    """
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        try:
            return json.dumps(value)
        except (TypeError, ValueError):
            return str(value)
    if isinstance(value, str):
        return value
    return str(value)


class Database:
    """SQLite database manager for Odoo index."""

    def __init__(self, db_path: Path):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        # Create parent directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._pool: Optional['AsyncConnectionPool'] = None
        self._init_schema()

    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic commit/rollback."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    async def get_pool(self) -> 'AsyncConnectionPool':
        """Get or create async connection pool."""
        if self._pool is None:
            self._pool = AsyncConnectionPool(self.db_path, pool_size=10)
            await self._pool.initialize()
        return self._pool

    @asynccontextmanager
    async def get_async_connection(self):
        """Get an async database connection with automatic commit/rollback."""
        pool = await self.get_pool()
        conn = await pool.acquire()
        try:
            yield conn
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise
        finally:
            await pool.release(conn)

    async def close_pool(self):
        """Close the async connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    def _init_schema(self):
        """Create database schema if it doesn't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Main indexed items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS indexed_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    parent_name TEXT,
                    module TEXT NOT NULL,
                    attributes TEXT,
                    dependency_depth INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(item_type, name, parent_name, module)
                )
            """)

            # References table for file locations (one-to-many)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS item_references (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    line_number INTEGER NOT NULL,
                    reference_type TEXT NOT NULL,
                    context TEXT,
                    FOREIGN KEY (item_id) REFERENCES indexed_items(id) ON DELETE CASCADE
                )
            """)

            # File tracking for incremental indexing
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    module TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for fast lookups
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_type ON indexed_items(item_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_name ON indexed_items(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_parent ON indexed_items(parent_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_module ON indexed_items(module)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_type_name ON indexed_items(item_type, name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dependency_depth ON indexed_items(dependency_depth)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ref_item_id ON item_references(item_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ref_file ON item_references(file_path)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_path ON file_metadata(file_path)")

            logger.info(f"Database schema initialized at {self.db_path}")

    def clear_all(self):
        """Clear all data from database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM item_references")
            cursor.execute("DELETE FROM indexed_items")
            cursor.execute("DELETE FROM file_metadata")
            logger.info("Database cleared")

    # Async methods for efficient concurrent indexing

    async def upsert_item_async(self, conn: aiosqlite.Connection, item_type: str, name: str,
                               parent_name: Optional[str], module: str,
                               attributes: dict, dependency_depth: int = 0) -> int:
        """Async version of upsert_item."""
        cursor = await conn.cursor()

        # Sanitize string parameters - convert lists/dicts to JSON strings
        item_type = sanitize_db_param(item_type)
        name = sanitize_db_param(name)
        parent_name = sanitize_db_param(parent_name)
        module = sanitize_db_param(module)

        try:
            attributes_json = json.dumps(attributes) if attributes else None
        except (TypeError, ValueError) as e:
            logger.warning(f"Failed to serialize attributes for {item_type}.{name}: {e}. Attributes: {attributes}")
            attributes_json = json.dumps({k: str(v) for k, v in attributes.items()}) if attributes else None

        # Try to get existing item
        await cursor.execute("""
            SELECT id FROM indexed_items
            WHERE item_type = ? AND name = ? AND parent_name IS ? AND module = ?
        """, (item_type, name, parent_name, module))

        row = await cursor.fetchone()

        if row:
            # Update existing
            item_id = row[0]
            await cursor.execute("""
                UPDATE indexed_items
                SET attributes = ?, dependency_depth = ?, created_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (attributes_json, dependency_depth, item_id))

            # Delete old references (will be re-added)
            await cursor.execute("DELETE FROM item_references WHERE item_id = ?", (item_id,))
        else:
            # Insert new
            await cursor.execute("""
                INSERT INTO indexed_items (item_type, name, parent_name, module, attributes, dependency_depth)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (item_type, name, parent_name, module, attributes_json, dependency_depth))
            item_id = cursor.lastrowid

        return item_id

    async def add_reference_async(self, conn: aiosqlite.Connection, item_id: int,
                                 file_path: str, line_number: int,
                                 reference_type: str, context: Optional[str] = None):
        """Async version of add_reference."""
        cursor = await conn.cursor()

        # Sanitize string parameters - convert lists/dicts to JSON strings
        file_path = sanitize_db_param(file_path)
        reference_type = sanitize_db_param(reference_type)
        context = sanitize_db_param(context)

        await cursor.execute("""
            INSERT INTO item_references (item_id, file_path, line_number, reference_type, context)
            VALUES (?, ?, ?, ?, ?)
        """, (item_id, file_path, line_number, reference_type, context))

    async def update_file_metadata_async(self, conn: aiosqlite.Connection, file_path: str,
                                        module: str, file_hash: str):
        """Async version of update_file_metadata."""
        cursor = await conn.cursor()

        # Sanitize string parameters
        file_path = sanitize_db_param(file_path)
        module = sanitize_db_param(module)
        file_hash = sanitize_db_param(file_hash)

        await cursor.execute("""
            INSERT OR REPLACE INTO file_metadata (file_path, module, file_hash, last_indexed)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (file_path, module, file_hash))

    async def get_file_hash_async(self, file_path: str) -> Optional[str]:
        """Async version of get_file_hash."""
        async with self.get_async_connection() as conn:
            cursor = await conn.cursor()
            file_path = sanitize_db_param(file_path)
            await cursor.execute("SELECT file_hash FROM file_metadata WHERE file_path = ?", (file_path,))
            row = await cursor.fetchone()
            return row[0] if row else None

    async def delete_file_references_async(self, conn: aiosqlite.Connection, file_path: str):
        """Async version of delete_file_references."""
        cursor = await conn.cursor()
        file_path = sanitize_db_param(file_path)
        await cursor.execute("DELETE FROM item_references WHERE file_path = ?", (file_path,))

    async def store_items_async(self, items: list[dict], file_path: str, module_name: str,
                               file_hash: Optional[str] = None, module_depth: int = 0):
        """Store items in database asynchronously (one transaction per file).

        Args:
            items: List of items to store
            file_path: File path
            module_name: Module name
            file_hash: File hash for change tracking
            module_depth: Module dependency depth (default: 0)
        """
        async with self.get_async_connection() as conn:
            # Delete old references from this file
            await self.delete_file_references_async(conn, file_path)

            # Store each item
            for item in items:
                # Upsert item
                item_id = await self.upsert_item_async(
                    conn,
                    item['item_type'],
                    item['name'],
                    item.get('parent_name'),
                    item['module'],
                    item.get('attributes', {}),
                    module_depth
                )

                # Add references
                for ref in item.get('references', []):
                    await self.add_reference_async(
                        conn,
                        item_id,
                        ref['file_path'],
                        ref['line_number'],
                        ref['reference_type'],
                        ref.get('context')
                    )

            # Update file metadata
            if file_hash:
                await self.update_file_metadata_async(conn, file_path, module_name, file_hash)


class AsyncConnectionPool:
    """Connection pool for async database operations."""

    def __init__(self, db_path: Path, pool_size: int = 10):
        """Initialize connection pool.

        Args:
            db_path: Path to SQLite database
            pool_size: Maximum number of connections
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=pool_size)
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize the connection pool."""
        async with self._lock:
            if self._initialized:
                return

            for _ in range(self.pool_size):
                conn = await aiosqlite.connect(str(self.db_path))
                conn.row_factory = aiosqlite.Row
                await self._pool.put(conn)

            self._initialized = True
            logger.info(f"Initialized async connection pool with {self.pool_size} connections")

    async def acquire(self) -> aiosqlite.Connection:
        """Acquire a connection from the pool."""
        if not self._initialized:
            await self.initialize()
        return await self._pool.get()

    async def release(self, conn: aiosqlite.Connection):
        """Release a connection back to the pool."""
        await self._pool.put(conn)

    async def close(self):
        """Close all connections in the pool."""
        async with self._lock:
            if not self._initialized:
                return

            while not self._pool.empty():
                conn = await self._pool.get()
                await conn.close()

            self._initialized = False
            logger.info("Closed async connection pool")
