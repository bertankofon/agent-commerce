"""
Simple image upload utility for Supabase Storage
"""
import os
import logging
from typing import Optional
from fastapi import UploadFile
from database.supabase.client import get_supabase_client

logger = logging.getLogger(__name__)


async def upload_product_image(
    image_file: UploadFile,
    agent_id: str,
    product_index: int
) -> Optional[str]:
    """
    Upload a product image to Supabase Storage.
    
    Args:
        image_file: The uploaded file
        agent_id: UUID of the agent
        product_index: Index of the product (0, 1, 2, etc.)
    
    Returns:
        Public URL of the uploaded image, or None if upload fails
    """
    try:
        client = get_supabase_client()
        
        # Read file content
        file_content = await image_file.read()
        
        # Check file size (5MB max)
        if len(file_content) > 5 * 1024 * 1024:
            logger.error(f"File too large: {len(file_content)} bytes")
            return None
        
        # Get file extension
        filename = image_file.filename or "image.jpg"
        ext = filename.split('.')[-1] if '.' in filename else 'jpg'
        
        # Create path: images/{agent_id}/product_{index}.{ext}
        file_path = f"images/{agent_id}/product_{product_index}.{ext}"
        
        logger.info(f"Uploading image to products bucket: {file_path}")
        
        # Upload to Supabase Storage
        response = client.storage.from_("products").upload(
            path=file_path,
            file=file_content,
            file_options={
                "content-type": image_file.content_type or "image/jpeg",
                "upsert": "true"  # Overwrite if exists
            }
        )
        
        # Get public URL
        public_url = client.storage.from_("products").get_public_url(file_path)
        
        logger.info(f"✓ Image uploaded successfully: {public_url}")
        return public_url
        
    except Exception as e:
        logger.error(f"Failed to upload product image: {str(e)}")
        return None

