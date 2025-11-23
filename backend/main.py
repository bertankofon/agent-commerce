import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middleware import RequestLoggingMiddleware, DummyAuthMiddleware
from routes.agent.routes import router as agent_router
from routes.negotiation.routes import router as negotiation_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Agent Commerce API",
    description="FastAPI backend for agent deployment and management",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(DummyAuthMiddleware)

# Include routers
app.include_router(agent_router)
app.include_router(negotiation_router)


@app.get("/health")
async def health_check():
    """
    Health check endpoint for Docker and monitoring.
    """
    return {"status": "healthy", "service": "agent-commerce-api"}


@app.get("/")
async def root():
    """
    Root endpoint.
    """
    return {
        "message": "Agent Commerce API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable, default to 8000
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )

