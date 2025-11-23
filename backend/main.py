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
from routes.negotiation.history_routes import router as negotiation_history_router
from routes.auth.routes import router as auth_router
from routes.market.routes import router as market_router

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
# Get allowed origins from environment variable or use defaults
allowed_origins_env = os.getenv("CORS_ORIGINS", "")
cors_allow_all = os.getenv("CORS_ALLOW_ALL", "true").lower() == "true"  # Default to true for development

if allowed_origins_env:
    # Parse comma-separated origins from environment variable
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
elif cors_allow_all:
    # Allow all origins (useful for development and Railway deployments)
    allowed_origins = ["*"]
else:
    # Default origins for development
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

logger.info(f"CORS configured with origins: {allowed_origins}")

# When allow_origins=["*"], allow_credentials must be False (CORS security restriction)
allow_credentials = "*" not in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(DummyAuthMiddleware)

# Include routers
app.include_router(agent_router)
app.include_router(negotiation_router)
app.include_router(negotiation_history_router)
app.include_router(auth_router)
app.include_router(market_router)


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

