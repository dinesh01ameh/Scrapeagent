"""
Database Connection and Configuration
Supabase/PostgreSQL integration for SwissKnife AI Scraper
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
import asyncpg
from supabase import create_client, Client
import os
from datetime import datetime

from config.settings import get_settings
from utils.logging import LoggingMixin
from utils.exceptions import DatabaseError


class DatabaseConnection(LoggingMixin):
    """
    Database connection manager for PostgreSQL/Supabase
    """
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.pool: Optional[asyncpg.Pool] = None
        self.supabase_client: Optional[Client] = None
        self.is_connected = False
        
    async def initialize(self):
        """Initialize database connections"""
        try:
            self.logger.info("Initializing database connections...")
            
            # Initialize PostgreSQL connection pool
            if self.settings.DATABASE_URL:
                await self._initialize_postgres_pool()
            
            # Initialize Supabase client
            if self.settings.SUPABASE_URL and self.settings.SUPABASE_KEY:
                await self._initialize_supabase_client()
            
            self.is_connected = True
            self.logger.info("Database connections initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")
    
    async def _initialize_postgres_pool(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.settings.DATABASE_URL,
                min_size=self.settings.DATABASE_MIN_CONNECTIONS,
                max_size=self.settings.DATABASE_MAX_CONNECTIONS,
                command_timeout=self.settings.DATABASE_TIMEOUT,
                server_settings={
                    'jit': 'off'  # Disable JIT for better performance on small queries
                }
            )
            self.logger.info("PostgreSQL connection pool created")
            
        except Exception as e:
            self.logger.error(f"PostgreSQL pool creation failed: {e}")
            raise DatabaseError(f"PostgreSQL connection failed: {e}")
    
    async def _initialize_supabase_client(self):
        """Initialize Supabase client"""
        try:
            self.supabase_client = create_client(
                self.settings.SUPABASE_URL,
                self.settings.SUPABASE_KEY
            )
            
            # Test connection
            response = self.supabase_client.table('users').select('id').limit(1).execute()
            self.logger.info("Supabase client initialized and tested")
            
        except Exception as e:
            self.logger.error(f"Supabase client initialization failed: {e}")
            raise DatabaseError(f"Supabase connection failed: {e}")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        if not self.pool:
            raise DatabaseError("Database pool not initialized")
        
        async with self.pool.acquire() as connection:
            try:
                yield connection
            except Exception as e:
                self.logger.error(f"Database operation failed: {e}")
                raise DatabaseError(f"Database operation failed: {e}")
    
    async def execute_query(
        self, 
        query: str, 
        *args, 
        fetch: str = "none"
    ) -> Any:
        """
        Execute database query
        
        Args:
            query: SQL query string
            *args: Query parameters
            fetch: "none", "one", "all", or "val"
            
        Returns:
            Query result based on fetch type
        """
        async with self.get_connection() as conn:
            try:
                if fetch == "none":
                    return await conn.execute(query, *args)
                elif fetch == "one":
                    return await conn.fetchrow(query, *args)
                elif fetch == "all":
                    return await conn.fetch(query, *args)
                elif fetch == "val":
                    return await conn.fetchval(query, *args)
                else:
                    raise ValueError(f"Invalid fetch type: {fetch}")
                    
            except Exception as e:
                self.logger.error(f"Query execution failed: {query[:100]}... Error: {e}")
                raise DatabaseError(f"Query execution failed: {e}")
    
    async def execute_transaction(self, queries: List[Dict[str, Any]]) -> List[Any]:
        """
        Execute multiple queries in a transaction
        
        Args:
            queries: List of query dictionaries with 'query', 'args', and 'fetch' keys
            
        Returns:
            List of query results
        """
        async with self.get_connection() as conn:
            async with conn.transaction():
                results = []
                try:
                    for query_info in queries:
                        query = query_info['query']
                        args = query_info.get('args', [])
                        fetch = query_info.get('fetch', 'none')
                        
                        if fetch == "none":
                            result = await conn.execute(query, *args)
                        elif fetch == "one":
                            result = await conn.fetchrow(query, *args)
                        elif fetch == "all":
                            result = await conn.fetch(query, *args)
                        elif fetch == "val":
                            result = await conn.fetchval(query, *args)
                        else:
                            raise ValueError(f"Invalid fetch type: {fetch}")
                        
                        results.append(result)
                    
                    return results
                    
                except Exception as e:
                    self.logger.error(f"Transaction failed: {e}")
                    raise DatabaseError(f"Transaction failed: {e}")
    
    def get_supabase_client(self) -> Client:
        """Get Supabase client"""
        if not self.supabase_client:
            raise DatabaseError("Supabase client not initialized")
        return self.supabase_client
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        health_status = {
            "postgres": {"status": "unknown", "latency_ms": None},
            "supabase": {"status": "unknown", "latency_ms": None},
            "overall": "unknown"
        }
        
        # Check PostgreSQL
        if self.pool:
            try:
                start_time = datetime.now()
                await self.execute_query("SELECT 1", fetch="val")
                latency = (datetime.now() - start_time).total_seconds() * 1000
                
                health_status["postgres"] = {
                    "status": "healthy",
                    "latency_ms": round(latency, 2),
                    "pool_size": self.pool.get_size(),
                    "pool_max_size": self.pool.get_max_size(),
                    "pool_min_size": self.pool.get_min_size()
                }
            except Exception as e:
                health_status["postgres"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Check Supabase
        if self.supabase_client:
            try:
                start_time = datetime.now()
                self.supabase_client.table('users').select('id').limit(1).execute()
                latency = (datetime.now() - start_time).total_seconds() * 1000
                
                health_status["supabase"] = {
                    "status": "healthy",
                    "latency_ms": round(latency, 2)
                }
            except Exception as e:
                health_status["supabase"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Overall status
        postgres_healthy = health_status["postgres"]["status"] == "healthy"
        supabase_healthy = health_status["supabase"]["status"] == "healthy"
        
        if postgres_healthy and supabase_healthy:
            health_status["overall"] = "healthy"
        elif postgres_healthy or supabase_healthy:
            health_status["overall"] = "degraded"
        else:
            health_status["overall"] = "unhealthy"
        
        return health_status
    
    async def close(self):
        """Close database connections"""
        try:
            if self.pool:
                await self.pool.close()
                self.logger.info("PostgreSQL connection pool closed")
            
            # Supabase client doesn't need explicit closing
            self.is_connected = False
            self.logger.info("Database connections closed")
            
        except Exception as e:
            self.logger.error(f"Error closing database connections: {e}")


class DatabaseMigration(LoggingMixin):
    """
    Database migration manager
    """
    
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__()
        self.db = db_connection
    
    async def run_migrations(self, migration_dir: str = "database/migrations"):
        """Run database migrations"""
        try:
            self.logger.info("Starting database migrations...")
            
            # Create migrations table if it doesn't exist
            await self._create_migrations_table()
            
            # Get applied migrations
            applied_migrations = await self._get_applied_migrations()
            
            # Get migration files
            migration_files = self._get_migration_files(migration_dir)
            
            # Apply new migrations
            for migration_file in migration_files:
                if migration_file not in applied_migrations:
                    await self._apply_migration(migration_file, migration_dir)
            
            self.logger.info("Database migrations completed successfully")
            
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            raise DatabaseError(f"Migration failed: {e}")
    
    async def _create_migrations_table(self):
        """Create migrations tracking table"""
        query = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id SERIAL PRIMARY KEY,
            migration_name VARCHAR(255) UNIQUE NOT NULL,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """
        await self.db.execute_query(query)
    
    async def _get_applied_migrations(self) -> List[str]:
        """Get list of applied migrations"""
        query = "SELECT migration_name FROM schema_migrations ORDER BY applied_at"
        rows = await self.db.execute_query(query, fetch="all")
        return [row['migration_name'] for row in rows]
    
    def _get_migration_files(self, migration_dir: str) -> List[str]:
        """Get sorted list of migration files"""
        if not os.path.exists(migration_dir):
            return []
        
        files = [f for f in os.listdir(migration_dir) if f.endswith('.sql')]
        return sorted(files)
    
    async def _apply_migration(self, migration_file: str, migration_dir: str):
        """Apply a single migration"""
        migration_path = os.path.join(migration_dir, migration_file)
        
        try:
            with open(migration_path, 'r') as f:
                migration_sql = f.read()
            
            # Execute migration in transaction
            queries = [
                {'query': migration_sql, 'fetch': 'none'},
                {
                    'query': 'INSERT INTO schema_migrations (migration_name) VALUES ($1)',
                    'args': [migration_file],
                    'fetch': 'none'
                }
            ]
            
            await self.db.execute_transaction(queries)
            self.logger.info(f"Applied migration: {migration_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to apply migration {migration_file}: {e}")
            raise DatabaseError(f"Migration {migration_file} failed: {e}")


# Global database connection instance
_db_connection: Optional[DatabaseConnection] = None


async def get_database() -> DatabaseConnection:
    """Get global database connection instance"""
    global _db_connection
    
    if _db_connection is None:
        _db_connection = DatabaseConnection()
        await _db_connection.initialize()
    
    return _db_connection


async def close_database():
    """Close global database connection"""
    global _db_connection
    
    if _db_connection:
        await _db_connection.close()
        _db_connection = None
