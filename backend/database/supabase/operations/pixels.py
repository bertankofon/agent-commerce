"""
Pixel Claims Operations for Supabase

Handles marketplace pixel claiming, querying, and validation.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from supabase import Client

logger = logging.getLogger(__name__)


class PixelsOperations:
    """Operations for the pixel_claims table in Supabase."""
    
    def __init__(self, client: Client):
        self.client = client
        self.table = "pixel_claims"
    
    def claim_pixels(
        self, 
        agent_id: UUID, 
        pixels: List[Tuple[int, int]]
    ) -> List[Dict[str, Any]]:
        """
        Claim multiple pixels for an agent.
        
        Args:
            agent_id: UUID of the merchant agent
            pixels: List of (x, y) coordinates to claim
        
        Returns:
            List of created pixel claim records
        
        Raises:
            ValueError: If any pixel is already claimed or out of bounds
        """
        try:
            # Validate all pixels first (50x20 grid)
            for x, y in pixels:
                if not (0 <= x < 50 and 0 <= y < 20):
                    raise ValueError(f"Pixel ({x}, {y}) is out of bounds (0-49, 0-19)")
                
                # Check if pixel is already claimed
                existing = self.client.table(self.table)\
                    .select("id")\
                    .eq("x", x)\
                    .eq("y", y)\
                    .execute()
                
                if existing.data:
                    raise ValueError(f"Pixel ({x}, {y}) is already claimed")
            
            # Check max 50 pixels limit
            if len(pixels) > 50:
                raise ValueError(f"Cannot claim more than 50 pixels (requested: {len(pixels)})")
            
            # Prepare data for batch insert
            claims_data = [
                {
                    "agent_id": str(agent_id),
                    "x": x,
                    "y": y
                }
                for x, y in pixels
            ]
            
            # Insert all claims
            response = self.client.table(self.table).insert(claims_data).execute()
            
            if not response.data:
                raise ValueError("Failed to claim pixels: no data returned")
            
            logger.info(f"Claimed {len(pixels)} pixels for agent {agent_id}")
            return response.data
            
        except Exception as e:
            logger.error(f"Error claiming pixels: {str(e)}")
            raise
    
    def get_all_claims(self) -> List[Dict[str, Any]]:
        """
        Get all pixel claims in the marketplace.
        
        Returns:
            List of all pixel claim records with agent info
        """
        try:
            response = self.client.table(self.table)\
                .select("*, agents(name, category, avatar_url)")\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting all claims: {str(e)}")
            raise
    
    def get_claims_by_agent(self, agent_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all pixel claims for a specific agent.
        
        Args:
            agent_id: UUID of the merchant agent
        
        Returns:
            List of pixel claim records
        """
        try:
            response = self.client.table(self.table)\
                .select("*")\
                .eq("agent_id", str(agent_id))\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting claims for agent {agent_id}: {str(e)}")
            raise
    
    def is_pixel_available(self, x: int, y: int) -> bool:
        """
        Check if a pixel is available for claiming.
        
        Args:
            x: X coordinate (0-49)
            y: Y coordinate (0-49)
        
        Returns:
            True if available, False if already claimed
        """
        try:
            if not (0 <= x < 50 and 0 <= y < 20):
                return False
            
            response = self.client.table(self.table)\
                .select("id")\
                .eq("x", x)\
                .eq("y", y)\
                .execute()
            
            return len(response.data or []) == 0
            
        except Exception as e:
            logger.error(f"Error checking pixel availability: {str(e)}")
            raise
    
    def get_available_pixels_in_area(
        self, 
        x_start: int, 
        y_start: int, 
        x_end: int, 
        y_end: int
    ) -> List[Tuple[int, int]]:
        """
        Get all available pixels in a rectangular area.
        
        Args:
            x_start: Start X coordinate
            y_start: Start Y coordinate
            x_end: End X coordinate
            y_end: End Y coordinate
        
        Returns:
            List of available (x, y) coordinates
        """
        try:
            # Get all claimed pixels in the area
            response = self.client.table(self.table)\
                .select("x, y")\
                .gte("x", x_start)\
                .lte("x", x_end)\
                .gte("y", y_start)\
                .lte("y", y_end)\
                .execute()
            
            claimed_set = {(pixel["x"], pixel["y"]) for pixel in (response.data or [])}
            
            # Generate all pixels in area and filter out claimed ones
            available = []
            for x in range(x_start, x_end + 1):
                for y in range(y_start, y_end + 1):
                    if 0 <= x < 50 and 0 <= y < 20 and (x, y) not in claimed_set:
                        available.append((x, y))
            
            return available
            
        except Exception as e:
            logger.error(f"Error getting available pixels in area: {str(e)}")
            raise
    
    def delete_claims_by_agent(self, agent_id: UUID) -> int:
        """
        Delete all pixel claims for an agent (when agent is deleted).
        
        Args:
            agent_id: UUID of the merchant agent
        
        Returns:
            Number of claims deleted
        """
        try:
            response = self.client.table(self.table)\
                .delete()\
                .eq("agent_id", str(agent_id))\
                .execute()
            
            count = len(response.data or [])
            logger.info(f"Deleted {count} pixel claims for agent {agent_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error deleting claims for agent {agent_id}: {str(e)}")
            raise
    
    def get_marketplace_stats(self) -> Dict[str, Any]:
        """
        Get marketplace statistics.
        
        Returns:
            Dictionary with stats (total pixels, claimed, free, by category)
        """
        try:
            # Get total claimed pixels
            claims_response = self.client.table(self.table)\
                .select("id", count="exact")\
                .execute()
            
            claimed_count = claims_response.count or 0
            
            # Get category breakdown
            agents_response = self.client.table("agents")\
                .select("category, pixel_count")\
                .gt("pixel_count", 0)\
                .execute()
            
            by_category = {}
            for agent in (agents_response.data or []):
                category = agent.get("category", "UNCATEGORIZED")
                pixel_count = agent.get("pixel_count", 0)
                by_category[category] = by_category.get(category, 0) + pixel_count
            
            return {
                "total_pixels": 1000,  # 50x20
                "claimed_pixels": claimed_count,
                "free_pixels": 1000 - claimed_count,
                "utilization_percent": round((claimed_count / 1000) * 100, 2),
                "by_category": by_category
            }
            
        except Exception as e:
            logger.error(f"Error getting marketplace stats: {str(e)}")
            raise

