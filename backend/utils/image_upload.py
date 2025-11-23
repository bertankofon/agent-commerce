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
    product_index: int,
    image_index: int = 0
) -> Optional[str]:
    """
    Upload a product image to Supabase Storage and return a signed URL valid for 100 years.
    
    Args:
        image_file: The uploaded file
        agent_id: UUID of the agent
        product_index: Index of the product (0, 1, 2, etc.)
        image_index: Index of the image for this product (0, 1, 2, etc.)
    
    Returns:
        Signed URL of the uploaded image valid for 100 years, or None if upload fails
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
        
        # Create path: images/{agent_id}/product_{product_index}/image_{image_index}.{ext}
        file_path = f"images/{agent_id}/product_{product_index}/image_{image_index}.{ext}"
        
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
        
        # Generate signed URL valid for 100 years (3,153,600,000 seconds)
        expiration_seconds = 100 * 365 * 24 * 60 * 60  # 100 years
        try:
            signed_url_response = client.storage.from_("products").create_signed_url(
                path=file_path,
                expires_in=expiration_seconds
            )
            
            if signed_url_response and 'signedURL' in signed_url_response:
                signed_url = signed_url_response['signedURL']
                logger.info(f"✓ Image uploaded successfully with 100-year URL: {signed_url}")
                return signed_url
            else:
                # Fallback to public URL if signed URL format is unexpected
                logger.warning(f"Signed URL response format unexpected, falling back to public URL")
                public_url = client.storage.from_("products").get_public_url(file_path)
                logger.info(f"✓ Image uploaded successfully (public URL): {public_url}")
                return public_url
        except Exception as url_error:
            # Fallback to public URL if signed URL generation fails
            logger.warning(f"Failed to generate signed URL: {str(url_error)}, using public URL")
            public_url = client.storage.from_("products").get_public_url(file_path)
            logger.info(f"✓ Image uploaded successfully (public URL fallback): {public_url}")
            return public_url
        
    except Exception as e:
        logger.error(f"Failed to upload product image: {str(e)}")
        return None

