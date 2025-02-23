import asyncio
import logging
from image_service import ImageService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fal_response():
    """Test function to check FAL AI response format"""
    service = ImageService()
    
    # Test with a simple prompt
    prompt = "A serene mountain landscape at sunset, professional photography style"
    logger.info(f"Testing FAL AI with prompt: {prompt}")
    
    # Generate image and get raw response
    result = await service.generate_image(prompt)
    
    # Log the response structure
    logger.info("Response structure:")
    logger.info(f"Result type: {type(result)}")
    if isinstance(result, dict):
        logger.info(f"Available keys: {result.keys()}")
        logger.info(f"Full response: {result}")
        
        # Check for URL
        if 'url' in result:
            logger.info(f"Image URL: {result['url']}")
    else:
        logger.error("Response is not a dictionary")

if __name__ == "__main__":
    asyncio.run(test_fal_response()) 