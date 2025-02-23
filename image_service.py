import os
import logging
import asyncio
import fal_client
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        self.fal_key = os.getenv('FAL_KEY')
        if not self.fal_key:
            raise ValueError("FAL_KEY environment variable is required")

    async def generate_image(self, prompt: str, style: str = "realistic_image", additional_params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Generate an image using FAL AI
        Returns the raw response from FAL AI containing image data and URL
        """
        try:
            # Prepare request parameters
            image_params = {
                **(additional_params or {}),
                "quality": 85  # Good quality but smaller file size
            }

            logger.info('Sending request to Fal AI:', {
                "prompt": prompt,
                "style": style,
                "additional_params": image_params
            })

            # Submit request to FAL AI using the client library
            handler = await fal_client.submit_async(
                "fal-ai/flux-pro/v1.1-ultra",
                arguments={
                    "prompt": prompt,
                    **image_params
                }
            )

            # Process events and logs
            async for event in handler.iter_events(with_logs=True):
                logger.info(f"FAL AI event: {event}")

            # Get the final result
            result = await handler.get()
            logger.info('Received response from Fal AI:', {
                "result": result,
                "type": type(result).__name__
            })

            if not result or not isinstance(result.get('images'), list) or not result['images']:
                logger.error("Invalid response from Fal AI")
                return None

            # Return the first generated image data
            return result['images'][0]

        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return None

    async def generate_images_for_slides(self, slides: list) -> list:
        """Generate images for slides that need them"""
        for slide in slides:
            if slide.get('type') == 'IMAGE_CENTERED' and 'imagePlaceholder' in slide.get('content', {}):
                prompt = slide['content']['imagePlaceholder']
                image_url = await self.generate_image(prompt)
                if image_url:
                    slide['content']['imageUrl'] = image_url
                    del slide['content']['imagePlaceholder']
        return slides 

    async def test_fal_response(self):
        """Test function to check FAL AI response format"""
        try:
            prompt = "A serene mountain landscape at sunset, professional photography style"
            logger.info(f"Testing FAL AI with prompt: {prompt}")

            # Submit request to FAL AI
            handler = await fal_client.submit_async(
                "fal-ai/flux-pro/v1.1-ultra",
                arguments={
                    "prompt": prompt,
                    "quality": 85
                }
            )

            # Log all events
            async for event in handler.iter_events(with_logs=True):
                logger.info(f"Event received: {event}")

            # Get final result and log its structure
            result = await handler.get()
            logger.info("Final result structure:")
            logger.info(f"Result type: {type(result)}")
            logger.info(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
            logger.info(f"Full result: {result}")

            if isinstance(result, dict) and 'images' in result:
                for i, image in enumerate(result['images']):
                    logger.info(f"Image {i} structure:")
                    logger.info(f"Image type: {type(image)}")
                    logger.info(f"Image keys: {image.keys() if isinstance(image, dict) else 'Not a dict'}")
                    logger.info(f"Image data: {image}")

            return result

        except Exception as e:
            logger.error(f"Error in test: {str(e)}")
            return None

# Add test execution code
if __name__ == "__main__":
    async def run_test():
        service = ImageService()
        await service.test_fal_response()

    asyncio.run(run_test()) 