"""
Session Management Service
Handles user authentication, session creation, and state management
"""

import secrets
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

from database.connection import DatabaseConnection
from database.repositories import RepositoryManager
from config.settings import get_settings
from utils.logging import LoggingMixin
from utils.exceptions import AuthenticationError, AuthorizationError, NotFoundError


class SessionManager(LoggingMixin):
    """
    Manages user sessions, authentication, and authorization
    """
    
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__()
        self.db = db_connection
        self.repos = RepositoryManager(db_connection)
        self.settings = get_settings()
        
        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # JWT settings
        self.jwt_secret = self.settings.JWT_SECRET_KEY
        self.jwt_algorithm = "HS256"
        self.jwt_expiration = timedelta(hours=24)
        
        # Session settings
        self.session_expiration = timedelta(days=30)
        
        self.logger.info("SessionManager initialized")
    
    async def create_user(
        self,
        email: str,
        password: str,
        username: Optional[str] = None,
        full_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new user account
        
        Args:
            email: User email address
            password: Plain text password
            username: Optional username
            full_name: Optional full name
            
        Returns:
            Created user data (without password hash)
        """
        try:
            # Check if user already exists
            existing_user = await self.repos.users.get_by_email(email)
            if existing_user:
                raise AuthenticationError("User with this email already exists")
            
            # Hash password
            password_hash = self.pwd_context.hash(password)
            
            # Generate API key
            api_key = self._generate_api_key()
            
            # Create user
            user_data = {
                "email": email,
                "username": username,
                "password_hash": password_hash,
                "full_name": full_name,
                "api_key": api_key,
                "is_active": True,
                "is_verified": False,
                "subscription_tier": "free"
            }
            
            user = await self.repos.users.create(user_data)
            
            # Remove sensitive data from response
            user.pop("password_hash", None)
            
            self.logger.info(f"User created: {email}")
            return user
            
        except Exception as e:
            self.logger.error(f"User creation failed: {e}")
            raise AuthenticationError(f"User creation failed: {e}")
    
    async def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user with email and password
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            User data if authentication successful
        """
        try:
            # Get user by email
            user = await self.repos.users.get_by_email(email)
            if not user:
                raise AuthenticationError("Invalid email or password")
            
            # Check if user is active
            if not user.get("is_active", False):
                raise AuthenticationError("Account is deactivated")
            
            # Verify password
            if not self.pwd_context.verify(password, user["password_hash"]):
                raise AuthenticationError("Invalid email or password")
            
            # Update last login
            await self.repos.users.update_last_login(user["id"])
            
            # Remove sensitive data
            user.pop("password_hash", None)
            
            self.logger.info(f"User authenticated: {email}")
            return user
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            raise AuthenticationError(f"Authentication failed: {e}")
    
    async def authenticate_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        Authenticate user with API key
        
        Args:
            api_key: User API key
            
        Returns:
            User data if authentication successful
        """
        try:
            user = await self.repos.users.get_by_api_key(api_key)
            if not user:
                raise AuthenticationError("Invalid API key")
            
            # Remove sensitive data
            user.pop("password_hash", None)
            
            return user
            
        except Exception as e:
            self.logger.error(f"API key authentication failed: {e}")
            raise AuthenticationError(f"API key authentication failed: {e}")
    
    async def create_session(
        self,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        expires_in_days: int = 30
    ) -> Dict[str, Any]:
        """
        Create a new user session
        
        Args:
            user_id: User ID
            name: Optional session name
            description: Optional session description
            expires_in_days: Session expiration in days
            
        Returns:
            Session data with token
        """
        try:
            # Generate session token
            session_token = self._generate_session_token()
            
            # Calculate expiration
            expires_at = datetime.now() + timedelta(days=expires_in_days)
            
            # Create session
            session_data = {
                "user_id": user_id,
                "session_token": session_token,
                "name": name or "Default Session",
                "description": description,
                "expires_at": expires_at,
                "is_active": True
            }
            
            session = await self.repos.sessions.create(session_data)
            
            self.logger.info(f"Session created for user: {user_id}")
            return session
            
        except Exception as e:
            self.logger.error(f"Session creation failed: {e}")
            raise AuthenticationError(f"Session creation failed: {e}")
    
    async def get_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Get session by token
        
        Args:
            session_token: Session token
            
        Returns:
            Session data if valid, None otherwise
        """
        try:
            session = await self.repos.sessions.get_by_token(session_token)
            return session
            
        except Exception as e:
            self.logger.error(f"Get session failed: {e}")
            return None
    
    async def validate_session(self, session_token: str) -> Dict[str, Any]:
        """
        Validate session and return user data
        
        Args:
            session_token: Session token
            
        Returns:
            User data if session is valid
        """
        try:
            # Get session
            session = await self.get_session(session_token)
            if not session:
                raise AuthenticationError("Invalid session token")
            
            # Get user
            user = await self.repos.users.get_by_id(session["user_id"])
            if not user or not user.get("is_active", False):
                raise AuthenticationError("User account is inactive")
            
            # Remove sensitive data
            user.pop("password_hash", None)
            
            return {
                "user": user,
                "session": session
            }
            
        except Exception as e:
            self.logger.error(f"Session validation failed: {e}")
            raise AuthenticationError(f"Session validation failed: {e}")
    
    async def deactivate_session(self, session_token: str) -> bool:
        """
        Deactivate a session (logout)
        
        Args:
            session_token: Session token to deactivate
            
        Returns:
            True if successful
        """
        try:
            session = await self.get_session(session_token)
            if not session:
                return False
            
            success = await self.repos.sessions.deactivate_session(session["id"])
            
            if success:
                self.logger.info(f"Session deactivated: {session['id']}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Session deactivation failed: {e}")
            return False
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all active sessions for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of active sessions
        """
        try:
            return await self.repos.sessions.get_user_sessions(user_id)
        except Exception as e:
            self.logger.error(f"Get user sessions failed: {e}")
            return []
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            count = await self.repos.cleanup_expired_sessions()
            if count > 0:
                self.logger.info(f"Cleaned up {count} expired sessions")
            return count
        except Exception as e:
            self.logger.error(f"Session cleanup failed: {e}")
            return 0
    
    async def generate_jwt_token(self, user_id: str, session_id: str) -> str:
        """
        Generate JWT token for API access
        
        Args:
            user_id: User ID
            session_id: Session ID
            
        Returns:
            JWT token string
        """
        try:
            payload = {
                "user_id": user_id,
                "session_id": session_id,
                "exp": datetime.utcnow() + self.jwt_expiration,
                "iat": datetime.utcnow()
            }
            
            token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            return token
            
        except Exception as e:
            self.logger.error(f"JWT token generation failed: {e}")
            raise AuthenticationError(f"Token generation failed: {e}")
    
    async def validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload if valid
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Validate session is still active
            session = await self.repos.sessions.get_by_id(payload["session_id"])
            if not session or not session.get("is_active", False):
                raise AuthenticationError("Session is no longer active")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
        except Exception as e:
            self.logger.error(f"JWT token validation failed: {e}")
            raise AuthenticationError(f"Token validation failed: {e}")
    
    async def change_password(
        self, 
        user_id: str, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """
        Change user password
        
        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
            
        Returns:
            True if successful
        """
        try:
            # Get user
            user = await self.repos.users.get_by_id(user_id)
            if not user:
                raise NotFoundError("User not found")
            
            # Verify current password
            if not self.pwd_context.verify(current_password, user["password_hash"]):
                raise AuthenticationError("Current password is incorrect")
            
            # Hash new password
            new_password_hash = self.pwd_context.hash(new_password)
            
            # Update password
            await self.repos.users.update(user_id, {"password_hash": new_password_hash})
            
            self.logger.info(f"Password changed for user: {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Password change failed: {e}")
            raise AuthenticationError(f"Password change failed: {e}")
    
    async def regenerate_api_key(self, user_id: str) -> str:
        """
        Regenerate API key for user
        
        Args:
            user_id: User ID
            
        Returns:
            New API key
        """
        try:
            new_api_key = self._generate_api_key()
            
            await self.repos.users.update(user_id, {"api_key": new_api_key})
            
            self.logger.info(f"API key regenerated for user: {user_id}")
            return new_api_key
            
        except Exception as e:
            self.logger.error(f"API key regeneration failed: {e}")
            raise AuthenticationError(f"API key regeneration failed: {e}")
    
    def _generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    def _generate_api_key(self) -> str:
        """Generate secure API key"""
        return f"sk_{secrets.token_urlsafe(32)}"
    
    async def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        try:
            total_sessions = await self.repos.sessions.count()
            active_sessions = await self.repos.sessions.count({"is_active": True})
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "inactive_sessions": total_sessions - active_sessions
            }
            
        except Exception as e:
            self.logger.error(f"Get session statistics failed: {e}")
            return {}
