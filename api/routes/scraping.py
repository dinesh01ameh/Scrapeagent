"""
Main scraping API endpoints
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl, Field

from core.scraper import SwissKnifeScraper
from main import get_scraper
from utils.exceptions import ScrapingError

router = APIRouter()


class ScrapeRequest(BaseModel):
    """Basic scrape request model"""
    url: HttpUrl
    query: Optional[str] = Field(None, description="Natural language query or extraction instructions")
    extraction_config: Optional[Dict[str, Any]] = Field(None, description="Custom extraction configuration")
    session_id: Optional[str] = Field(None, description="Session ID for context tracking")


class NaturalLanguageScrapeRequest(BaseModel):
    """Natural language scrape request model"""
    url: HttpUrl
    query: str = Field(..., description="Natural language query describing what to extract")
    session_id: Optional[str] = Field(None, description="Session ID for context tracking")


class MultiModalScrapeRequest(BaseModel):
    """Multi-modal scrape request model"""
    url: HttpUrl
    content_types: List[str] = Field(default=["text", "images"], description="Types of content to process")
    query: Optional[str] = Field(None, description="Optional query for content analysis")


class AmbiguityResolutionRequest(BaseModel):
    """Request to resolve an ambiguous natural language query"""
    url: HttpUrl
    original_query: str = Field(..., description="The original ambiguous query")
    clarification: str = Field(..., description="User's clarification to resolve ambiguity")
    session_id: Optional[str] = Field(None, description="Session ID for context tracking")


class MultiStepConversationRequest(BaseModel):
    """Request to start a multi-step conversation"""
    session_id: str = Field(..., description="Session ID for conversation tracking")
    initial_query: str = Field(..., description="Initial query to start the conversation")


class ConversationContinueRequest(BaseModel):
    """Request to continue a multi-step conversation"""
    session_id: str = Field(..., description="Session ID for conversation tracking")
    user_response: str = Field(..., description="User's response to continue the conversation")


class ScrapeResponse(BaseModel):
    """Scrape response model"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    requires_clarification: Optional[bool] = None
    ambiguity_check: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


@router.post("/", response_model=ScrapeResponse)
async def scrape_url(
    request: ScrapeRequest,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """
    Basic scraping endpoint with adaptive extraction
    """
    try:
        result = await scraper.scrape(
            url=str(request.url),
            query=request.query,
            extraction_config=request.extraction_config,
            session_id=request.session_id
        )
        
        return ScrapeResponse(
            success=True,
            data=result
        )
        
    except ScrapingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/natural-language", response_model=ScrapeResponse)
async def natural_language_scrape(
    request: NaturalLanguageScrapeRequest,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """
    Natural language scraping endpoint
    
    Examples:
    - "Get all products under $50 with 4+ star reviews"
    - "Extract all email addresses and phone numbers from the contact page"
    - "Find all job listings posted in the last 30 days with salary information"
    """
    try:
        result = await scraper.natural_language_scrape(
            url=str(request.url),
            query=request.query,
            session_id=request.session_id
        )
        
        # Handle both regular results and clarification requests
        if result.get("requires_clarification", False):
            return ScrapeResponse(
                success=True,
                requires_clarification=True,
                ambiguity_check=result.get("ambiguity_check", {}),
                message=result.get("message", "Clarification needed"),
                data=result
            )
        else:
            return ScrapeResponse(
                success=True,
                data=result
            )

    except ScrapingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/resolve-ambiguity", response_model=ScrapeResponse)
async def resolve_ambiguous_query(
    request: AmbiguityResolutionRequest,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """
    Resolve an ambiguous natural language query with user clarification

    This endpoint is used when the initial natural language query was ambiguous
    and the system requested clarification from the user.
    """
    try:
        result = await scraper.resolve_ambiguous_query(
            url=str(request.url),
            original_query=request.original_query,
            clarification=request.clarification,
            session_id=request.session_id
        )

        # Handle both resolved results and continued clarification requests
        if result.get("requires_clarification", False):
            return ScrapeResponse(
                success=True,
                requires_clarification=True,
                ambiguity_check=result.get("ambiguity_check", {}),
                message=result.get("message", "Additional clarification needed"),
                data=result
            )
        else:
            return ScrapeResponse(
                success=True,
                data=result
            )

    except ScrapingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/conversation/{session_id}/summary")
async def get_conversation_summary(
    session_id: str,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """
    Get a summary of the conversation history for a session

    Returns conversation patterns, common targets, and usage statistics.
    """
    try:
        if not scraper.nlp_processor:
            raise HTTPException(status_code=400, detail="Natural Language Interface not enabled")

        summary = scraper.nlp_processor.get_conversation_summary(session_id)
        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/conversation/{session_id}/predictions")
async def get_next_intent_predictions(
    session_id: str,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """
    Get predictions for what the user might want to do next

    Based on conversation history and patterns, suggests likely next actions.
    """
    try:
        if not scraper.nlp_processor:
            raise HTTPException(status_code=400, detail="Natural Language Interface not enabled")

        predictions = scraper.nlp_processor.predict_next_intent(session_id)
        return predictions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/admin/cleanup-sessions")
async def cleanup_old_sessions(
    max_age_hours: int = 24,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """
    Clean up old conversation sessions

    Removes sessions older than the specified number of hours to prevent memory bloat.
    """
    try:
        if not scraper.nlp_processor:
            raise HTTPException(status_code=400, detail="Natural Language Interface not enabled")

        cleanup_result = scraper.nlp_processor.cleanup_old_sessions(max_age_hours)
        return cleanup_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/natural-language/complex", response_model=ScrapeResponse)
async def complex_natural_language_scrape(
    request: NaturalLanguageScrapeRequest,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """
    Natural language scraping with complex conditional logic support

    This endpoint specifically handles complex queries with conditional logic,
    multi-step instructions, and error handling strategies.

    Examples of complex queries:
    - "Get all products under $50, but if price is missing, check the description for price info"
    - "First extract all job titles, then for each job get the salary if available, otherwise mark as 'not specified'"
    - "Find all reviews with 4+ stars, unless there are fewer than 10 reviews, then get all reviews"
    """
    try:
        result = await scraper.natural_language_scrape(
            url=str(request.url),
            query=request.query,
            session_id=request.session_id,
            check_ambiguity=True  # Enable complex logic processing
        )

        # Handle both regular results and clarification requests
        if result.get("requires_clarification", False):
            return ScrapeResponse(
                success=True,
                requires_clarification=True,
                ambiguity_check=result.get("ambiguity_check", {}),
                message=result.get("message", "Clarification needed"),
                data=result
            )
        else:
            return ScrapeResponse(
                success=True,
                data=result
            )

    except ScrapingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/query/analyze")
async def analyze_query_complexity(
    query: str,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """
    Analyze the complexity of a natural language query without executing it

    Returns information about detected conditions, complexity score, and execution strategy.
    """
    try:
        if not scraper.nlp_processor:
            raise HTTPException(status_code=400, detail="Natural Language Interface not enabled")

        # Parse intent and entities
        intent = await scraper.nlp_processor.parse_intent(query)
        entities = await scraper.nlp_processor.extract_entities(query)

        # Parse complex conditions
        conditions = await scraper.nlp_processor.parse_complex_conditions(query, intent)

        # Detect ambiguity
        ambiguity_check = await scraper.nlp_processor.detect_ambiguity(query, intent, entities)

        return {
            "query": query,
            "intent": {
                "type": intent.type,
                "confidence": intent.confidence,
                "target_data": intent.target_data,
                "filters": intent.filters
            },
            "entities": [
                {
                    "type": entity.type,
                    "value": entity.value,
                    "confidence": entity.confidence
                } for entity in entities
            ],
            "complexity_analysis": {
                "complexity_score": conditions.get("complexity_score", 0.0),
                "has_complex_logic": conditions.get("has_complex_logic", False),
                "conditional_rules": len(conditions.get("conditional_rules", [])),
                "fallback_strategies": len(conditions.get("fallback_strategies", [])),
                "multi_step_logic": len(conditions.get("multi_step_logic", [])),
                "error_handling": len(conditions.get("error_handling", [])),
                "validation_rules": len(conditions.get("validation_rules", []))
            },
            "ambiguity_check": ambiguity_check,
            "recommended_execution_mode": "complex" if conditions.get("has_complex_logic", False) else "standard",
            "estimated_execution_time": len(conditions.get("conditional_rules", [])) * 5 + len(conditions.get("multi_step_logic", [])) * 3
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/conversation/start")
async def start_multi_step_conversation(
    request: MultiStepConversationRequest,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """
    Start a multi-step conversation for building complex scraping tasks

    This endpoint allows users to build complex scraping configurations through
    a guided conversation, breaking down complex requests into manageable steps.
    """
    try:
        if not scraper.nlp_processor:
            raise HTTPException(status_code=400, detail="Natural Language Interface not enabled")

        result = await scraper.nlp_processor.start_multi_step_conversation(
            session_id=request.session_id,
            initial_query=request.initial_query
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/conversation/continue")
async def continue_multi_step_conversation(
    request: ConversationContinueRequest,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """
    Continue a multi-step conversation

    Process user responses and guide them through the next steps of building
    their scraping configuration.
    """
    try:
        if not scraper.nlp_processor:
            raise HTTPException(status_code=400, detail="Natural Language Interface not enabled")

        result = await scraper.nlp_processor.continue_multi_step_conversation(
            session_id=request.session_id,
            user_response=request.user_response
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/conversation/{session_id}/status")
async def get_conversation_status(
    session_id: str,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """
    Get the current status of a multi-step conversation

    Returns information about the current step, completed steps, and overall progress.
    """
    try:
        if not scraper.nlp_processor:
            raise HTTPException(status_code=400, detail="Natural Language Interface not enabled")

        if session_id not in scraper.nlp_processor.context_memory:
            raise HTTPException(status_code=404, detail="Session not found")

        context = scraper.nlp_processor.context_memory[session_id]
        multi_step_state = context.get("multi_step_state", {})

        return {
            "session_id": session_id,
            "is_active": multi_step_state.get("active", False),
            "current_step": multi_step_state.get("current_step", 0),
            "total_steps": multi_step_state.get("total_steps", 0),
            "completed_steps": len(multi_step_state.get("completed_steps", [])),
            "pending_steps": len(multi_step_state.get("pending_steps", [])),
            "progress_percentage": (
                (len(multi_step_state.get("completed_steps", [])) / multi_step_state.get("total_steps", 1)) * 100
                if multi_step_state.get("total_steps", 0) > 0 else 0
            ),
            "conversation_started": context.get("created_at"),
            "last_updated": context.get("last_updated"),
            "has_final_config": bool(multi_step_state.get("final_config"))
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/conversation/{session_id}/execute")
async def execute_conversation_config(
    session_id: str,
    url: HttpUrl,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """
    Execute the final configuration from a completed multi-step conversation

    This endpoint runs the scraping task using the configuration built through
    the multi-step conversation process.
    """
    try:
        if not scraper.nlp_processor:
            raise HTTPException(status_code=400, detail="Natural Language Interface not enabled")

        if session_id not in scraper.nlp_processor.context_memory:
            raise HTTPException(status_code=404, detail="Session not found")

        context = scraper.nlp_processor.context_memory[session_id]
        multi_step_state = context.get("multi_step_state", {})
        final_config = multi_step_state.get("final_config")

        if not final_config:
            raise HTTPException(status_code=400, detail="No final configuration available. Complete the conversation first.")

        # Execute scraping with the conversation-built configuration
        result = await scraper.scrape(
            url=str(url),
            query="Multi-step conversation execution",
            extraction_config=final_config,
            session_id=session_id
        )

        # Add conversation metadata
        result["conversation_metadata"] = {
            "session_id": session_id,
            "total_conversation_steps": multi_step_state.get("total_steps", 0),
            "execution_mode": "multi_step_conversation",
            "config_source": "conversation_builder"
        }

        return ScrapeResponse(
            success=True,
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/multimodal", response_model=ScrapeResponse)
async def multimodal_scrape(
    request: MultiModalScrapeRequest,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """
    Multi-modal content processing endpoint
    
    Supported content types:
    - text: Text extraction with formatting
    - images: Image analysis and OCR
    - pdfs: PDF content extraction
    - tables: Table detection and extraction
    - videos: Video metadata extraction
    - audio: Audio content analysis
    """
    try:
        result = await scraper.multimodal_scrape(
            url=str(request.url),
            content_types=request.content_types,
            query=request.query
        )
        
        return ScrapeResponse(
            success=True,
            data=result
        )
        
    except ScrapingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=Dict[str, Any])
async def batch_scrape(
    requests: List[ScrapeRequest],
    background_tasks: BackgroundTasks,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """
    Batch scraping endpoint for multiple URLs
    """
    if len(requests) > 100:  # Limit batch size
        raise HTTPException(status_code=400, detail="Batch size cannot exceed 100 URLs")
    
    # For now, return a job ID and process in background
    # In a full implementation, this would use a task queue like Celery
    job_id = f"batch_{hash(str(requests))}"
    
    return {
        "job_id": job_id,
        "status": "queued",
        "total_urls": len(requests),
        "message": "Batch job queued for processing"
    }


@router.get("/job/{job_id}", response_model=Dict[str, Any])
async def get_job_status(job_id: str):
    """
    Get status of a batch scraping job
    """
    # Placeholder implementation
    return {
        "job_id": job_id,
        "status": "not_implemented",
        "message": "Job status tracking not yet implemented"
    }
