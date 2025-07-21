import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
from .schemas import UnifiedAnalysisResult
from .service import detection_aggregator
from ..core.security import security_validator

router = APIRouter(prefix="/api", tags=["detection"])

# In-memory storage for demo purposes
analysis_results: Dict[str, UnifiedAnalysisResult] = {}

@router.post("/analyze", response_model=UnifiedAnalysisResult)
async def analyze_file(
    request: Request,
    file: UploadFile = File(...)
):
    """
    Analyze uploaded file using multiple AI detection providers
    """
    try:
        # Get client IP for rate limiting
        client_ip = request.client.host
        
        # Check rate limits
        security_validator.check_rate_limit(client_ip)
        
        # Read file content
        content = await file.read()
        
        # Validate file
        security_validator.validate_file_size(content)
        safe_filename = security_validator.validate_filename(file.filename)
        content_type = security_validator.validate_file_type(content)
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Perform analysis
        result = await detection_aggregator.analyze_file(
            file_id=file_id,
            filename=safe_filename,
            content=content,
            content_type=content_type
        )
        
        # Store result for later retrieval
        analysis_results[file_id] = result
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

@router.get("/analysis/{file_id}", response_model=UnifiedAnalysisResult)
async def get_analysis_result(file_id: str):
    """
    Retrieve analysis result by file ID
    """
    if file_id not in analysis_results:
        raise HTTPException(
            status_code=404,
            detail="Analysis result not found"
        )
    
    return analysis_results[file_id]

@router.get("/detections")
async def list_recent_analyses(limit: int = 10):
    """
    List recent analysis results
    """
    # Get most recent analyses
    recent_results = list(analysis_results.values())
    recent_results.sort(key=lambda x: x.created_at, reverse=True)
    
    # Return summary information
    summaries = []
    for result in recent_results[:limit]:
        summaries.append({
            "file_id": result.file_id,
            "filename": result.original_filename,
            "file_type": result.file_type,
            "risk_level": result.overall_risk_level,
            "confidence": result.overall_confidence,
            "total_matches": result.total_matches,
            "created_at": result.created_at.isoformat()
        })
    
    return {"analyses": summaries, "total": len(analysis_results)}

@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    # Check provider configurations
    provider_status = {}
    for provider in detection_aggregator.providers:
        provider_status[provider.provider_name] = {
            "configured": provider.check_configuration(),
            "status": "ready" if provider.check_configuration() else "not_configured"
        }
    
    return {
        "status": "healthy",
        "providers": provider_status,
        "total_analyses": len(analysis_results)
    }