import asyncio
import logging
from image_service import ImageService
from image_storage import ImageStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_supabase_storage():
    """Test image storage with direct URL construction"""
    image_service = ImageService()
    storage_service = ImageStorage()
    
    # First, let's test URL construction
    test_filename = "test_image_123_abc.jpg"
    constructed_url = storage_service._construct_public_url(test_filename)
    logger.info(f"Constructed URL format: {constructed_url}")
    
    # Now let's test with a real image
    prompt = "A simple test image of a red circle on white background"
    logger.info(f"Generating test image with prompt: {prompt}")
    
    result = await image_service.generate_image(prompt)
    if not result or 'url' not in result:
        logger.error("Failed to generate test image")
        return
    
    logger.info(f"FAL AI image URL: {result['url']}")
    logger.info(f"Image dimensions: {result.get('width')}x{result.get('height')}")
    
    # Store in Supabase
    logger.info("Storing image in Supabase...")
    stored_url = await storage_service.store_image_from_url(result['url'])
    
    if stored_url:
        logger.info(f"Image stored successfully")
        logger.info(f"Storage URL: {stored_url}")
    else:
        logger.error("Failed to store image")

if __name__ == "__main__":
    asyncio.run(test_supabase_storage()) 