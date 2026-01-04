"""FastAPI application for leads monitoring."""

import sys
from pathlib import Path

# Add parent directory to path to import storage module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ui.api.routes import leads, stats

app = FastAPI(
    title="Leads Monitoring API",
    description="API for food-finder leads database",
    version="1.0.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(leads.router, prefix="/api/leads", tags=["leads"])


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Leads Monitoring API"}


@app.get("/api/health")
def health():
    """Health check for API."""
    return {"status": "healthy"}
