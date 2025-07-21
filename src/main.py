from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Import routers and middleware
from .aggregation.router import router as detection_router
from .core.middleware import setup_middleware

# Create FastAPI application
app = FastAPI(
    title="Cara AI Detection Platform",
    description="Professional AI-powered digital likeness and IP detection",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup middleware (CORS, logging, etc.)
setup_middleware(app)

# Include API routes
app.include_router(detection_router)

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Root endpoint - serve the HTML interface
@app.get("/")
async def serve_frontend():
    """Serve the main HTML interface"""
    return FileResponse("static/index.html")

# Additional health check at root level
@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "Cara AI Detection Platform is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )