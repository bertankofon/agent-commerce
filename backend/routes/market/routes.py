"""
Market/Pixel Marketplace API Routes

Endpoints for pixel claiming, querying, and marketplace stats.
"""

import logging
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from uuid import UUID

from database.supabase.operations import PixelsOperations
from database.supabase.client import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/market", tags=["market"])


# Pydantic models
class PixelCoordinate(BaseModel):
    x: int
    y: int


class ClaimPixelsRequest(BaseModel):
    agent_id: str
    pixels: List[PixelCoordinate]


class PixelClaimResponse(BaseModel):
    success: bool
    claimed_count: int
    message: str


class MarketStatsResponse(BaseModel):
    total_pixels: int
    claimed_pixels: int
    free_pixels: int
    utilization_percent: float
    by_category: Dict[str, int]


@router.get("/pixels")
async def get_all_pixel_claims():
    """
    Get all pixel claims in the marketplace.
    Returns pixel coordinates with agent information.
    """
    try:
        supabase = get_supabase_client()
        pixels_ops = PixelsOperations(supabase)
        
        claims = pixels_ops.get_all_claims()
        
        return {
            "success": True,
            "pixels": claims,
            "count": len(claims)
        }
        
    except Exception as e:
        logger.error(f"Error getting pixel claims: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pixel claims: {str(e)}"
        )


@router.get("/pixels/agent/{agent_id}")
async def get_agent_pixel_claims(agent_id: str):
    """
    Get all pixel claims for a specific agent.
    """
    try:
        supabase = get_supabase_client()
        pixels_ops = PixelsOperations(supabase)
        
        claims = pixels_ops.get_claims_by_agent(UUID(agent_id))
        
        return {
            "success": True,
            "agent_id": agent_id,
            "pixels": claims,
            "count": len(claims)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid agent_id: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting agent pixel claims: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent pixel claims: {str(e)}"
        )


@router.post("/pixels/claim", response_model=PixelClaimResponse)
async def claim_pixels(request: ClaimPixelsRequest):
    """
    Claim pixels for an agent.
    Validates availability and max limit (150 pixels total per agent).
    Prevents race conditions with database UNIQUE constraint on (x, y).
    """
    try:
        supabase = get_supabase_client()
        pixels_ops = PixelsOperations(supabase)
        
        # Convert to list of tuples
        pixel_coords = [(p.x, p.y) for p in request.pixels]
        
        # Claim pixels
        claims = pixels_ops.claim_pixels(
            agent_id=UUID(request.agent_id),
            pixels=pixel_coords
        )
        
        # Update agent's pixel_count
        from database.supabase.operations import AgentsOperations
        agents_ops = AgentsOperations(supabase)
        
        # Get current pixel count for this agent
        all_claims = pixels_ops.get_claims_by_agent(UUID(request.agent_id))
        pixel_count = len(all_claims)
        
        # Update agent
        supabase.table("agents")\
            .update({"pixel_count": pixel_count})\
            .eq("id", request.agent_id)\
            .execute()
        
        return PixelClaimResponse(
            success=True,
            claimed_count=len(claims),
            message=f"Successfully claimed {len(claims)} pixels"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error claiming pixels: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to claim pixels: {str(e)}"
        )


@router.get("/pixels/available")
async def check_pixels_availability(x: int, y: int):
    """
    Check if a specific pixel is available.
    """
    try:
        supabase = get_supabase_client()
        pixels_ops = PixelsOperations(supabase)
        
        available = pixels_ops.is_pixel_available(x, y)
        
        return {
            "x": x,
            "y": y,
            "available": available
        }
        
    except Exception as e:
        logger.error(f"Error checking pixel availability: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check pixel availability: {str(e)}"
        )


@router.get("/stats", response_model=MarketStatsResponse)
async def get_marketplace_stats():
    """
    Get marketplace statistics.
    """
    try:
        supabase = get_supabase_client()
        pixels_ops = PixelsOperations(supabase)
        
        stats = pixels_ops.get_marketplace_stats()
        
        return MarketStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting marketplace stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get marketplace stats: {str(e)}"
        )


@router.get("/pixels/area")
async def get_available_pixels_in_area(
    x_start: int,
    y_start: int,
    x_end: int,
    y_end: int
):
    """
    Get all available pixels in a rectangular area.
    Useful for pixel selection UI.
    """
    try:
        supabase = get_supabase_client()
        pixels_ops = PixelsOperations(supabase)
        
        available = pixels_ops.get_available_pixels_in_area(
            x_start, y_start, x_end, y_end
        )
        
        return {
            "area": {
                "x_start": x_start,
                "y_start": y_start,
                "x_end": x_end,
                "y_end": y_end
            },
            "available_pixels": [{"x": x, "y": y} for x, y in available],
            "count": len(available)
        }
        
    except Exception as e:
        logger.error(f"Error getting available pixels in area: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available pixels in area: {str(e)}"
        )

