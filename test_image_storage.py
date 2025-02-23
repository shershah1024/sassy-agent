import asyncio
import logging
from image_service import ImageService
from image_storage import ImageStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_image_generation_and_storage():
    """Test generating an image with FAL AI and storing it in Supabase"""
    image_service = ImageService()
    storage_service = ImageStorage()
    
    # Generate image
    prompt = "A serene mountain landscape at sunset, professional photography style"
    logger.info(f"Generating image with prompt: {prompt}")
    
    result = await image_service.generate_image(prompt)
    if not result or 'url' not in result:
        logger.error("Failed to generate image")
        return
    
    logger.info(f"Image generated successfully: {result['url']}")
    
    # Store image in Supabase
    logger.info("Storing image in Supabase...")
    stored_url = await storage_service.store_image_from_url(result['url'])
    
    if stored_url:
        logger.info(f"Image stored successfully at: {stored_url}")
    else:
        logger.error("Failed to store image")

if __name__ == "__main__":
    asyncio.run(test_image_generation_and_storage()) 