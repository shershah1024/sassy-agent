import os
import asyncio
from typing import Optional, Dict, Any, Literal, List
from enum import Enum
import fal_client
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class ImageStyle(Enum):
    REALISTIC = "realistic_image"
    ARTISTIC = "artistic_image"
    TECHNICAL = "technical_diagram"
    MINIMALIST = "minimalist_design"

    @classmethod
    def from_string(cls, style_str: str) -> Optional['ImageStyle']:
        """Convert string to ImageStyle, handling nested styles"""
        try:
            # Handle case-insensitive matching
            style_str = style_str.upper() if style_str else None
            return cls[style_str] if style_str else None
        except (KeyError, AttributeError):
            logger.warning(f"Unknown style: {style_str}, falling back to REALISTIC")
            return cls.REALISTIC

class ImageSize(Enum):
    SQUARE_HD = "square_hd"  # 1024x1024
    LANDSCAPE_HD = "landscape_hd"  # 1024x768
    PORTRAIT_HD = "portrait_hd"  # 768x1024

class ImageRequest:
    def __init__(
        self,
        prompt: str,
        image_size: str = "square_hd",
        style: Optional[str] = None,
        colors: Optional[List[str]] = None
    ):
        self.prompt = prompt
        self.image_size = ImageSize(image_size)
        self.style = ImageStyle.from_string(style) if style else None
        if self.style is None and style is not None:
            logger.warning(f"Unknown style: {style}, falling back to default")
        self.colors = colors or []

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImageRequest':
        return cls(
            prompt=data["prompt"],
            image_size=data.get("image_size", "square_hd"),
            style=data.get("style"),
            colors=data.get("colors", [])
        )

class ImageGenerationService:
    def __init__(self):
        self.fal_key = os.getenv("FAL_KEY")
        if not self.fal_key:
            raise ValueError("FAL_KEY environment variable is not set")
        
        # Set the API key for fal-client
        fal_client.api_key = self.fal_key

    def _get_image_size(self, size: ImageSize) -> Dict[str, int]:
        """Get image dimensions based on size enum"""
        size_map = {
            ImageSize.SQUARE_HD: {"width": 1024, "height": 1024},
            ImageSize.LANDSCAPE_HD: {"width": 1024, "height": 768},
            ImageSize.PORTRAIT_HD: {"width": 768, "height": 1024}
        }
        return size_map[size]

    def _add_style_to_prompt(self, prompt: str, colors: Optional[List[str]] = None) -> str:
        """
        Enhance the prompt with colors
        """
        enhanced_prompt = prompt

        if colors and len(colors) > 0:
            color_str = " and ".join(colors)
            enhanced_prompt = f"{enhanced_prompt}, using colors: {color_str}"

        return enhanced_prompt

    async def generate_image(
        self, 
        request: ImageRequest,
        model: str = "fal-ai/recraft-v3",
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate an image using FAL AI's image generation models.
        
        Args:
            request (ImageRequest): The image generation request
            model (str): The model to use for generation (default: fal-ai/recraft-v3)
            additional_params (Dict[str, Any], optional): Additional parameters for the model
            
        Returns:
            Dict[str, Any]: The generation result containing image data and metadata
        """
        try:
            # Log the request details
            logger.info(f"Starting image generation process...")
            logger.info(f"Using model: {model}")
            logger.info(f"Image style: {request.style.value if request.style else 'None'}")
            
            # Enhance prompt with colors only
            enhanced_prompt = self._add_style_to_prompt(request.prompt, request.colors)
            logger.info(f"Enhanced prompt: {enhanced_prompt}")
            
            # Get image dimensions
            size_params = self._get_image_size(request.image_size)
            logger.info(f"Image size parameters: {size_params}")
            
            # Prepare the arguments
            arguments = {
                "prompt": enhanced_prompt,
                "image_format": "webp",  # Always use WebP format
                **size_params
            }
            
            # Add style as a separate parameter
            if request.style:
                arguments["style"] = request.style.value
            
            if additional_params:
                arguments.update(additional_params)

            logger.info(f"Sending request to FAL AI with arguments: {arguments}")

            # Submit the generation request
            logger.info("Submitting async request to FAL AI...")
            handler = await fal_client.submit_async(
                model,
                arguments=arguments
            )

            # Wait for the result with timeout handling
            logger.info("Waiting for image generation to complete...")
            try:
                result = await asyncio.wait_for(handler.get(), timeout=30.0)  # 30 second timeout
                logger.info("Image generation completed successfully")
                logger.info(f"Result structure: {result}")
                return result
            except asyncio.TimeoutError:
                logger.error("Image generation timed out after 30 seconds")
                raise Exception("Image generation timed out")

        except Exception as e:
            logger.error(f"Image generation failed: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {getattr(e, 'details', 'No details available')}")
            raise Exception(f"Image generation failed: {str(e)}")

    async def generate_image_with_progress(
        self, 
        request: ImageRequest,
        model: str = "fal-ai/recraft-v3",
        additional_params: Optional[Dict[str, Any]] = None
    ):
        """
        Generate an image with progress updates using FAL AI's image generation models.
        
        Args:
            request (ImageRequest): The image generation request
            model (str): The model to use for generation (default: fal-ai/recraft-v3)
            additional_params (Dict[str, Any], optional): Additional parameters for the model
            
        Yields:
            Dict[str, Any]: Progress updates and final generation result
        """
        try:
            # Enhance prompt with colors only
            enhanced_prompt = self._add_style_to_prompt(request.prompt, request.colors)
            
            # Get image dimensions
            size_params = self._get_image_size(request.image_size)
            
            # Prepare the arguments
            arguments = {
                "prompt": enhanced_prompt,
                "image_format": "webp",  # Always use WebP format
                **size_params
            }
            
            # Add style as a separate parameter
            if request.style:
                arguments["style"] = request.style.value
            
            if additional_params:
                arguments.update(additional_params)

            # Submit the generation request
            handler = await fal_client.submit_async(
                model,
                arguments=arguments
            )

            # Stream progress updates
            async for event in handler.iter_events(with_logs=True):
                yield event

            # Get and yield the final result
            result = await handler.get()
            yield result

        except Exception as e:
            raise Exception(f"Image generation failed: {str(e)}")

# Example usage
async def main():
    service = ImageGenerationService()
    
    # Test with JSON format
    request_data = {
        "prompt": "a red panda eating a bamboo in front of a poster that says 'recraft V3 now available at fal'",
        "image_size": "square_hd",
        "style": "realistic_image",
        "colors": []
    }
    
    request = ImageRequest.from_dict(request_data)
    result = await service.generate_image(request)
    print("Generation Result:", result)

if __name__ == "__main__":
    asyncio.run(main()) 