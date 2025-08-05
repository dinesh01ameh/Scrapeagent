"""
Data Repository Layer
Repository pattern implementation for data access operations
"""

import uuid
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import json
import hashlib

from database.connection import DatabaseConnection
from utils.logging import LoggingMixin
from utils.exceptions import DatabaseError, NotFoundError


class BaseRepository(LoggingMixin):
    """Base repository class with common CRUD operations"""
    
    def __init__(self, db_connection: DatabaseConnection, table_name: str):
        super().__init__()
        self.db = db_connection
        self.table_name = table_name
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record"""
        try:
            # Generate ID if not provided
            if 'id' not in data:
                data['id'] = str(uuid.uuid4())
            
            # Build insert query
            columns = list(data.keys())
            placeholders = [f'${i+1}' for i in range(len(columns))]
            values = list(data.values())
            
            query = f"""
                INSERT INTO {self.table_name} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING *
            """
            
            result = await self.db.execute_query(query, *values, fetch="one")
            return dict(result) if result else None
            
        except Exception as e:
            self.logger.error(f"Create operation failed for {self.table_name}: {e}")
            raise DatabaseError(f"Create operation failed: {e}")
    
    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get record by ID"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE id = $1"
            result = await self.db.execute_query(query, record_id, fetch="one")
            return dict(result) if result else None
            
        except Exception as e:
            self.logger.error(f"Get by ID failed for {self.table_name}: {e}")
            raise DatabaseError(f"Get by ID failed: {e}")
    
    async def update(self, record_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update record by ID"""
        try:
            if not data:
                return await self.get_by_id(record_id)
            
            # Build update query
            set_clauses = [f"{key} = ${i+2}" for i, key in enumerate(data.keys())]
            values = [record_id] + list(data.values())
            
            query = f"""
                UPDATE {self.table_name}
                SET {', '.join(set_clauses)}
                WHERE id = $1
                RETURNING *
            """
            
            result = await self.db.execute_query(query, *values, fetch="one")
            return dict(result) if result else None
            
        except Exception as e:
            self.logger.error(f"Update operation failed for {self.table_name}: {e}")
            raise DatabaseError(f"Update operation failed: {e}")
    
    async def delete(self, record_id: str) -> bool:
        """Delete record by ID"""
        try:
            query = f"DELETE FROM {self.table_name} WHERE id = $1"
            result = await self.db.execute_query(query, record_id)
            return "DELETE 1" in result
            
        except Exception as e:
            self.logger.error(f"Delete operation failed for {self.table_name}: {e}")
            raise DatabaseError(f"Delete operation failed: {e}")
    
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at DESC"
    ) -> List[Dict[str, Any]]:
        """List records with optional filters"""
        try:
            where_clauses = []
            values = []
            param_count = 0
            
            if filters:
                for key, value in filters.items():
                    param_count += 1
                    where_clauses.append(f"{key} = ${param_count}")
                    values.append(value)
            
            where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            query = f"""
                SELECT * FROM {self.table_name}
                {where_clause}
                ORDER BY {order_by}
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            
            values.extend([limit, offset])
            results = await self.db.execute_query(query, *values, fetch="all")
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"List operation failed for {self.table_name}: {e}")
            raise DatabaseError(f"List operation failed: {e}")
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters"""
        try:
            where_clauses = []
            values = []
            param_count = 0
            
            if filters:
                for key, value in filters.items():
                    param_count += 1
                    where_clauses.append(f"{key} = ${param_count}")
                    values.append(value)
            
            where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            query = f"SELECT COUNT(*) FROM {self.table_name} {where_clause}"
            result = await self.db.execute_query(query, *values, fetch="val")
            return result or 0
            
        except Exception as e:
            self.logger.error(f"Count operation failed for {self.table_name}: {e}")
            raise DatabaseError(f"Count operation failed: {e}")


class UserRepository(BaseRepository):
    """Repository for user management"""
    
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection, "users")
    
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            query = "SELECT * FROM users WHERE email = $1"
            result = await self.db.execute_query(query, email, fetch="one")
            return dict(result) if result else None
        except Exception as e:
            self.logger.error(f"Get user by email failed: {e}")
            raise DatabaseError(f"Get user by email failed: {e}")
    
    async def get_by_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get user by API key"""
        try:
            query = "SELECT * FROM users WHERE api_key = $1 AND is_active = true"
            result = await self.db.execute_query(query, api_key, fetch="one")
            return dict(result) if result else None
        except Exception as e:
            self.logger.error(f"Get user by API key failed: {e}")
            raise DatabaseError(f"Get user by API key failed: {e}")
    
    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp"""
        await self.update(user_id, {"last_login_at": datetime.now()})


class SessionRepository(BaseRepository):
    """Repository for session management"""
    
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection, "sessions")
    
    async def get_by_token(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get session by token"""
        try:
            query = """
                SELECT * FROM sessions 
                WHERE session_token = $1 
                AND is_active = true 
                AND (expires_at IS NULL OR expires_at > NOW())
            """
            result = await self.db.execute_query(query, session_token, fetch="one")
            return dict(result) if result else None
        except Exception as e:
            self.logger.error(f"Get session by token failed: {e}")
            raise DatabaseError(f"Get session by token failed: {e}")
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user"""
        return await self.list(
            filters={"user_id": user_id, "is_active": True},
            order_by="created_at DESC"
        )
    
    async def deactivate_session(self, session_id: str) -> bool:
        """Deactivate a session"""
        result = await self.update(session_id, {"is_active": False})
        return result is not None


class ProjectRepository(BaseRepository):
    """Repository for project management"""
    
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection, "projects")
    
    async def get_user_projects(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all projects for a user"""
        return await self.list(
            filters={"user_id": user_id},
            order_by="updated_at DESC"
        )


class ScrapingJobRepository(BaseRepository):
    """Repository for scraping job management"""
    
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection, "scraping_jobs")
    
    async def get_pending_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get pending scraping jobs"""
        return await self.list(
            filters={"status": "pending"},
            limit=limit,
            order_by="priority DESC, created_at ASC"
        )
    
    async def get_user_jobs(
        self, 
        user_id: str, 
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get jobs for a specific user"""
        filters = {"user_id": user_id}
        if status:
            filters["status"] = status
        
        return await self.list(
            filters=filters,
            order_by="created_at DESC"
        )
    
    async def update_job_status(
        self, 
        job_id: str, 
        status: str, 
        error_message: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update job status"""
        update_data = {"status": status}
        
        if status == "running":
            update_data["started_at"] = datetime.now()
        elif status in ["completed", "failed"]:
            update_data["completed_at"] = datetime.now()
        
        if error_message:
            update_data["error_message"] = error_message
        
        return await self.update(job_id, update_data)


class ScrapedContentRepository(BaseRepository):
    """Repository for scraped content management"""
    
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection, "scraped_content")
    
    async def create_content(
        self, 
        job_id: str,
        user_id: str,
        url: str,
        content_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create scraped content record"""
        # Generate content hash for duplicate detection
        content_hash = self._generate_content_hash(content_data.get("raw_content", ""))
        
        data = {
            "job_id": job_id,
            "user_id": user_id,
            "url": url,
            "content_hash": content_hash,
            **content_data
        }
        
        return await self.create(data)
    
    async def find_duplicate(self, content_hash: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Find duplicate content by hash"""
        try:
            query = """
                SELECT * FROM scraped_content 
                WHERE content_hash = $1 AND user_id = $2
                ORDER BY created_at DESC
                LIMIT 1
            """
            result = await self.db.execute_query(query, content_hash, user_id, fetch="one")
            return dict(result) if result else None
        except Exception as e:
            self.logger.error(f"Find duplicate failed: {e}")
            raise DatabaseError(f"Find duplicate failed: {e}")
    
    async def search_content(
        self, 
        user_id: str,
        query: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Full-text search in scraped content"""
        try:
            search_query = """
                SELECT *, ts_rank(to_tsvector('english', title || ' ' || raw_content), plainto_tsquery('english', $2)) as rank
                FROM scraped_content
                WHERE user_id = $1 
                AND (to_tsvector('english', title || ' ' || raw_content) @@ plainto_tsquery('english', $2))
                ORDER BY rank DESC, created_at DESC
                LIMIT $3
            """
            results = await self.db.execute_query(search_query, user_id, query, limit, fetch="all")
            return [dict(row) for row in results]
        except Exception as e:
            self.logger.error(f"Content search failed: {e}")
            raise DatabaseError(f"Content search failed: {e}")
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate SHA-256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()


class ExtractedEntityRepository(BaseRepository):
    """Repository for extracted entities"""
    
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection, "extracted_entities")
    
    async def create_entities(
        self, 
        content_id: str, 
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create multiple entities for content"""
        created_entities = []
        
        for entity in entities:
            entity_data = {
                "content_id": content_id,
                **entity
            }
            created_entity = await self.create(entity_data)
            created_entities.append(created_entity)
        
        return created_entities
    
    async def get_content_entities(self, content_id: str) -> List[Dict[str, Any]]:
        """Get all entities for content"""
        return await self.list(
            filters={"content_id": content_id},
            order_by="entity_type, entity_value"
        )


class ProxyUsageRepository(BaseRepository):
    """Repository for proxy usage tracking"""
    
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection, "proxy_usage")
    
    async def record_usage(
        self,
        job_id: str,
        proxy_id: str,
        success: bool,
        response_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Record proxy usage"""
        data = {
            "job_id": job_id,
            "proxy_id": proxy_id,
            "success": success,
            "response_time_ms": response_time_ms,
            "error_message": error_message,
            "metadata": metadata or {}
        }
        
        return await self.create(data)
    
    async def get_proxy_stats(self, proxy_id: str) -> Dict[str, Any]:
        """Get statistics for a specific proxy"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_uses,
                    COUNT(*) FILTER (WHERE success = true) as successful_uses,
                    COUNT(*) FILTER (WHERE success = false) as failed_uses,
                    AVG(response_time_ms) FILTER (WHERE success = true) as avg_response_time,
                    MAX(used_at) as last_used
                FROM proxy_usage
                WHERE proxy_id = $1
            """
            result = await self.db.execute_query(query, proxy_id, fetch="one")
            return dict(result) if result else {}
        except Exception as e:
            self.logger.error(f"Get proxy stats failed: {e}")
            raise DatabaseError(f"Get proxy stats failed: {e}")


class APIUsageRepository(BaseRepository):
    """Repository for API usage tracking"""
    
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection, "api_usage")
    
    async def record_api_call(
        self,
        user_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: int,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        api_key_used: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record API usage"""
        data = {
            "user_id": user_id,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "request_size": request_size,
            "response_size": response_size,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "api_key_used": api_key_used
        }
        
        return await self.create(data)
    
    async def get_user_usage_stats(
        self, 
        user_id: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get usage statistics for a user"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_calls,
                    COUNT(DISTINCT DATE(created_at)) as active_days,
                    AVG(response_time_ms) as avg_response_time,
                    SUM(request_size) as total_request_size,
                    SUM(response_size) as total_response_size
                FROM api_usage
                WHERE user_id = $1 AND created_at >= NOW() - INTERVAL '%s days'
            """ % days
            
            result = await self.db.execute_query(query, user_id, fetch="one")
            return dict(result) if result else {}
        except Exception as e:
            self.logger.error(f"Get user usage stats failed: {e}")
            raise DatabaseError(f"Get user usage stats failed: {e}")


class RepositoryManager:
    """
    Central manager for all repositories
    """

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

        # Initialize repositories
        self.users = UserRepository(db_connection)
        self.sessions = SessionRepository(db_connection)
        self.projects = ProjectRepository(db_connection)
        self.scraping_jobs = ScrapingJobRepository(db_connection)
        self.scraped_content = ScrapedContentRepository(db_connection)
        self.extracted_entities = ExtractedEntityRepository(db_connection)
        self.proxy_usage = ProxyUsageRepository(db_connection)
        self.api_usage = APIUsageRepository(db_connection)

    async def get_user_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a user"""
        try:
            # Get user info
            user = await self.users.get_by_id(user_id)
            if not user:
                raise NotFoundError("User not found")

            # Get statistics
            total_projects = await self.projects.count({"user_id": user_id})
            total_jobs = await self.scraping_jobs.count({"user_id": user_id})
            completed_jobs = await self.scraping_jobs.count({
                "user_id": user_id,
                "status": "completed"
            })
            total_content = await self.scraped_content.count({"user_id": user_id})

            # Get recent activity
            recent_jobs = await self.scraping_jobs.get_user_jobs(user_id)[:10]
            recent_content = await self.scraped_content.list(
                filters={"user_id": user_id},
                limit=10,
                order_by="created_at DESC"
            )

            return {
                "user": user,
                "statistics": {
                    "total_projects": total_projects,
                    "total_jobs": total_jobs,
                    "completed_jobs": completed_jobs,
                    "success_rate": completed_jobs / total_jobs if total_jobs > 0 else 0,
                    "total_content": total_content
                },
                "recent_activity": {
                    "jobs": recent_jobs,
                    "content": recent_content
                }
            }

        except Exception as e:
            raise DatabaseError(f"Failed to get dashboard data: {e}")

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            query = """
                UPDATE sessions
                SET is_active = false
                WHERE is_active = true
                AND expires_at IS NOT NULL
                AND expires_at < NOW()
            """
            result = await self.db.execute_query(query)
            # Extract number from result like "UPDATE 5"
            return int(result.split()[-1]) if result else 0

        except Exception as e:
            raise DatabaseError(f"Failed to cleanup sessions: {e}")

    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        try:
            stats = {}

            # User statistics
            stats["users"] = {
                "total": await self.users.count(),
                "active": await self.users.count({"is_active": True}),
                "verified": await self.users.count({"is_verified": True})
            }

            # Job statistics
            stats["jobs"] = {
                "total": await self.scraping_jobs.count(),
                "pending": await self.scraping_jobs.count({"status": "pending"}),
                "running": await self.scraping_jobs.count({"status": "running"}),
                "completed": await self.scraping_jobs.count({"status": "completed"}),
                "failed": await self.scraping_jobs.count({"status": "failed"})
            }

            # Content statistics
            stats["content"] = {
                "total": await self.scraped_content.count(),
                "duplicates": await self.scraped_content.count({"is_duplicate": True})
            }

            return stats

        except Exception as e:
            raise DatabaseError(f"Failed to get system statistics: {e}")
