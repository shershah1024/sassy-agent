import asyncio
import logging
from image_services import ImageGenerationService, ImageRequest, ImageStyle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_image_generation():
    service = ImageGenerationService()
    
    # Test logo generation
    logo_prompt = "A modern, minimalist logo for a tech company called Maitrise with abstract geometric shapes. Transparent background"
    logo_request = ImageRequest.from_dict({
        "prompt": logo_prompt,
        "image_size": "square_hd",
        "style": ImageStyle.LOGO.value,
    })
    
    logger.info("\nTesting logo generation...")
    result = await service.generate_image(logo_request)
    logger.info(f'Logo result URL: {result["images"][0]["url"]}')
    
    # Test realistic image generation
    realistic_prompt = "A serene mountain landscape with a lake reflection at sunset"
    realistic_request = ImageRequest.from_dict({
        "prompt": realistic_prompt,
        "image_size": "landscape_hd",
        "style": ImageStyle.REALISTIC.value,
        "colors": ["blue", "orange", "purple"]
    })
    
    logger.info("\nTesting realistic image generation...")
    result = await service.generate_image(realistic_request)
    logger.info(f'Realistic image result URL: {result["images"][0]["url"]}')

if __name__ == "__main__":
    asyncio.run(test_image_generation()) 