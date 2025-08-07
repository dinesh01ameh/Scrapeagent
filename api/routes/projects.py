"""
Projects API routes for SwissKnife AI Scraper
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from config.settings import get_settings
# from database.connection import get_database, DatabaseConnection
from api.routes.auth import verify_token, USERS_DB

# Temporary in-memory project storage (replace with database)
PROJECTS_DB = {}

# Setup
router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()
security = HTTPBearer()

# Pydantic models
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, pattern="^(active|inactive|archived)$")
    settings: Optional[Dict[str, Any]] = None

class Project(ProjectBase):
    id: str
    user_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class ProjectStats(BaseModel):
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    pending_jobs: int
    total_content: int
    success_rate: float
    avg_processing_time: float

class PaginatedProjects(BaseModel):
    data: List[Project]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool

class ProjectTemplate(BaseModel):
    id: str
    name: str
    description: str
    settings: Dict[str, Any]
    category: str

class CreateFromTemplate(BaseModel):
    template_id: str
    name: str
    description: Optional[str] = None

class DuplicateProject(BaseModel):
    name: str

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    try:
        payload = verify_token(credentials.credentials)
        email = payload.get("sub")
        user_id = payload.get("user_id")
        
        # For now, use the in-memory user store from auth
        # In production, this should query the database
        user = USERS_DB.get(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return {
            "id": str(user_id),
            "email": email,
            "full_name": user.get("full_name", "")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

@router.get("/", response_model=PaginatedProjects)
async def get_projects(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None, pattern="^(active|inactive|archived)$"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all projects for the current user with pagination and filtering"""
    try:
        user_id = current_user["id"]
        
        # Filter projects for current user
        user_projects = [p for p in PROJECTS_DB.values() if p["user_id"] == user_id]
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            user_projects = [
                p for p in user_projects 
                if search_lower in p["name"].lower() or 
                   (p.get("description") and search_lower in p["description"].lower())
            ]
        
        # Apply status filter
        if status:
            user_projects = [p for p in user_projects if p["status"] == status]
        
        # Sort by created_at desc
        user_projects.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Pagination
        total = len(user_projects)
        offset = (page - 1) * limit
        paginated_projects = user_projects[offset:offset + limit]
        
        projects = []
        for p in paginated_projects:
            projects.append(Project(
                id=p["id"],
                user_id=p["user_id"],
                name=p["name"],
                description=p.get("description"),
                status=p["status"],
                settings=p.get("settings", {}),
                created_at=p["created_at"],
                updated_at=p["updated_at"],
                metadata=p.get("metadata", {})
            ))
        
        return PaginatedProjects(
            data=projects,
            total=total,
            page=page,
            limit=limit,
            has_next=offset + limit < total,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch projects"
        )

@router.post("/", response_model=Project)
async def create_project(
    project_data: ProjectCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new project"""
    try:
        project_id = str(uuid4())
        now = datetime.utcnow()
        
        project = {
            "id": project_id,
            "user_id": current_user["id"],
            "name": project_data.name,
            "description": project_data.description,
            "status": "active",
            "settings": project_data.settings or {},
            "created_at": now,
            "updated_at": now,
            "metadata": {}
        }
        
        PROJECTS_DB[project_id] = project
        
        logger.info(f"Project created: {project_data.name} by {current_user['email']}")
        
        return Project(
            id=project["id"],
            user_id=project["user_id"],
            name=project["name"],
            description=project["description"],
            status=project["status"],
            settings=project["settings"],
            created_at=project["created_at"],
            updated_at=project["updated_at"],
            metadata=project["metadata"]
        )
        
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )

@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a single project by ID"""
    try:
        project = PROJECTS_DB.get(project_id)
        
        if not project or project["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return Project(
            id=project["id"],
            user_id=project["user_id"],
            name=project["name"],
            description=project["description"],
            status=project["status"],
            settings=project["settings"],
            created_at=project["created_at"],
            updated_at=project["updated_at"],
            metadata=project["metadata"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch project"
        )

@router.patch("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update a project"""
    try:
        project = PROJECTS_DB.get(project_id)
        
        if not project or project["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Update fields
        if project_data.name is not None:
            project["name"] = project_data.name
        if project_data.description is not None:
            project["description"] = project_data.description
        if project_data.status is not None:
            project["status"] = project_data.status
        if project_data.settings is not None:
            project["settings"] = project_data.settings
        
        project["updated_at"] = datetime.utcnow()
        
        logger.info(f"Project updated: {project_id} by {current_user['email']}")
        
        return Project(
            id=project["id"],
            user_id=project["user_id"],
            name=project["name"],
            description=project["description"],
            status=project["status"],
            settings=project["settings"],
            created_at=project["created_at"],
            updated_at=project["updated_at"],
            metadata=project["metadata"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        )

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a project"""
    try:
        project = PROJECTS_DB.get(project_id)
        
        if not project or project["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        del PROJECTS_DB[project_id]
        
        logger.info(f"Project deleted: {project_id} by {current_user['email']}")
        
        return {"message": "Project deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        )

@router.get("/{project_id}/stats", response_model=ProjectStats)
async def get_project_stats(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get project statistics"""
    try:
        project = PROJECTS_DB.get(project_id)
        
        if not project or project["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Return mock statistics for now
        return ProjectStats(
            total_jobs=0,
            completed_jobs=0,
            failed_jobs=0,
            pending_jobs=0,
            total_content=0,
            success_rate=0.0,
            avg_processing_time=0.0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch project statistics"
        )

@router.post("/{project_id}/duplicate", response_model=Project)
async def duplicate_project(
    project_id: str,
    duplicate_data: DuplicateProject,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Duplicate a project"""
    try:
        original = PROJECTS_DB.get(project_id)
        
        if not original or original["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Create duplicate
        new_project_id = str(uuid4())
        now = datetime.utcnow()
        
        new_project = {
            "id": new_project_id,
            "user_id": current_user["id"],
            "name": duplicate_data.name,
            "description": original["description"],
            "status": "active",
            "settings": original["settings"].copy(),
            "created_at": now,
            "updated_at": now,
            "metadata": original["metadata"].copy()
        }
        
        PROJECTS_DB[new_project_id] = new_project
        
        logger.info(f"Project duplicated: {project_id} -> {new_project_id} by {current_user['email']}")
        
        return Project(
            id=new_project["id"],
            user_id=new_project["user_id"],
            name=new_project["name"],
            description=new_project["description"],
            status=new_project["status"],
            settings=new_project["settings"],
            created_at=new_project["created_at"],
            updated_at=new_project["updated_at"],
            metadata=new_project["metadata"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error duplicating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to duplicate project"
        )

@router.get("/templates/", response_model=List[ProjectTemplate])
async def get_project_templates():
    """Get available project templates"""
    try:
        # For now, return static templates
        # In production, these could be stored in database
        templates = [
            ProjectTemplate(
                id="ecommerce",
                name="E-commerce Product Scraper",
                description="Template for scraping product information from e-commerce sites",
                category="E-commerce",
                settings={
                    "extraction_config": {
                        "fields": ["title", "price", "description", "images", "availability"],
                        "selectors": {
                            "title": "h1, .product-title",
                            "price": ".price, .cost",
                            "description": ".description, .product-description"
                        }
                    },
                    "proxy_config": {
                        "enabled": True,
                        "rotation": "per_request"
                    }
                }
            ),
            ProjectTemplate(
                id="news",
                name="News Article Scraper",
                description="Template for scraping news articles and blog posts",
                category="Content",
                settings={
                    "extraction_config": {
                        "fields": ["title", "content", "author", "date", "tags"],
                        "selectors": {
                            "title": "h1, .article-title",
                            "content": ".article-content, .post-content",
                            "author": ".author, .byline"
                        }
                    }
                }
            ),
            ProjectTemplate(
                id="social",
                name="Social Media Monitor",
                description="Template for monitoring social media posts and mentions",
                category="Social Media",
                settings={
                    "extraction_config": {
                        "fields": ["content", "author", "timestamp", "engagement"],
                        "rate_limit": {
                            "requests_per_minute": 30
                        }
                    }
                }
            )
        ]
        
        return templates
        
    except Exception as e:
        logger.error(f"Error fetching project templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch project templates"
        )

@router.post("/from-template/", response_model=Project)
async def create_from_template(
    template_data: CreateFromTemplate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a project from a template"""
    try:
        # Get templates
        templates = await get_project_templates()
        template = next((t for t in templates if t.id == template_data.template_id), None)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Create project from template
        project_id = str(uuid4())
        now = datetime.utcnow()
        
        metadata = {
            "created_from_template": template_data.template_id,
            "template_name": template.name
        }
        
        project = {
            "id": project_id,
            "user_id": current_user["id"],
            "name": template_data.name,
            "description": template_data.description or template.description,
            "status": "active",
            "settings": template.settings,
            "created_at": now,
            "updated_at": now,
            "metadata": metadata
        }
        
        PROJECTS_DB[project_id] = project
        
        logger.info(f"Project created from template: {template_data.template_id} by {current_user['email']}")
        
        return Project(
            id=project["id"],
            user_id=project["user_id"],
            name=project["name"],
            description=project["description"],
            status=project["status"],
            settings=project["settings"],
            created_at=project["created_at"],
            updated_at=project["updated_at"],
            metadata=project["metadata"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project from template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project from template"
        )