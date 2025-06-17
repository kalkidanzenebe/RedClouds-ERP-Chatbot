# backend/app/database.py

import aioodbc
import logging
from typing import Optional
from backend.app.config import settings # Make sure this import is correct

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.pool: Optional[aioodbc.Pool] = None

    async def connect(self):
        try:
            conn_str = (
                f"DRIVER={settings.db_driver};"
                f"SERVER={settings.db_server};"
                f"DATABASE={settings.db_name};"
                f"Trusted_Connection=yes;"
                f"{'PORT=' + str(settings.db_port) + ';' if settings.db_port else ''}"
            )
            self.pool = await aioodbc.create_pool(
                dsn=conn_str,
                minsize=settings.db_pool_min,
                maxsize=settings.db_pool_max,
                loop=None
            )
            logger.info("✅ SQL Server connection pool created")
        except Exception as e:
            logger.error(f"❌ SQL Server connection failed: {e}")
            raise

    async def disconnect(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("✅ SQL Server connection pool closed")

    async def execute_query(self, query: str, params: Optional[tuple] = None):
        if not self.pool:
            raise ConnectionError("Database pool not initialized.")
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params or ())
                rows = await cursor.fetchall()
                return rows

    async def execute_operation(self, query: str, params: Optional[tuple] = None):
        if not self.pool:
            raise ConnectionError("Database pool not initialized.")
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params or ())
                # For operations like INSERT/UPDATE/DELETE, usually no fetchall needed
                # If you need rowcount or lastrowid, you might add it here
            await conn.commit() # Ensure changes are committe
# THIS IS THE MISSING PART IF IT'S NOT THERE!
# Instantiate the DatabaseManager class at the module level
db_manager = DatabaseManager()

    