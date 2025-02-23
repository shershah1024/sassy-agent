import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel
import fal_client
from enum import Enum
from recraft_storage import RecraftStorage
from openai_utils import structured_openai_completion

logger = logging.getLogger(__name__)

class IllustrationStyle(str, Enum):
    POSTER_DIGITAL = "digital_illustration/2d_art_poster"     # For posters and marketing materials
    MODERN_MINIMAL = "digital_illustration/modern_folk"       # For clean, minimalist designs
    NEON_FUTURISTIC = "digital_illustration/neon_calm"       # For tech and futuristic themes
    BOLD_VECTOR = "vector_illustration/bold_stroke"          # For logos and brand assets
    REALISTIC = "realistic_image/natural_light"              # For realistic scenes
    URBAN = "digital_illustration/urban_glow"                # For urban and street themes
    POP_ART = "digital_illustration/pop_art"                 # For vibrant, eye-catching designs
    HAND_DRAWN = "digital_illustration/hand_drawn"           # For organic, sketchy feel
    PIXEL_ART = "digital_illustration/pixel_art"             # For retro, gaming style
    INFOGRAPHIC = "vector_illustration/infographical"        # For data visualization

class ImageSize(str, Enum):
    SQUARE_HD = "square_hd"           # 1080x1080 - High detail square format
    SQUARE = "square"                 # 800x800 - Standard square format
    PORTRAIT_4_3 = "portrait_4_3"     # 1080x1440 - Portrait format 4:3
    PORTRAIT_16_9 = "portrait_16_9"   # 1080x1920 - Portrait format 16:9
    LANDSCAPE_4_3 = "landscape_4_3"   # 1440x1080 - Landscape format 4:3
    LANDSCAPE_16_9 = "landscape_16_9" # 1920x1080 - Landscape format 16:9

    def get_dimensions(self) -> Dict[str, int]:
        """Get the pixel dimensions for this size format"""
        dimensions = {
            "square_hd": {"width": 1080, "height": 1080},
            "square": {"width": 800, "height": 800},
            "portrait_4_3": {"width": 1080, "height": 1440},
            "portrait_16_9": {"width": 1080, "height": 1920},
            "landscape_4_3": {"width": 1440, "height": 1080},
            "landscape_16_9": {"width": 1920, "height": 1080}
        }
        return dimensions[self.value]

class PosterContent(BaseModel):
    """Model for poster content and styling"""
    title: str
    description: str
    text_overlay: Optional[str] = None
    visual_style: IllustrationStyle
    size_format: ImageSize
    color_theme: Optional[str] = None
    mood: Optional[str] = None
    key_elements: Optional[List[str]] = None
    composition_notes: Optional[str] = None

class EmailContent(BaseModel):
    """Model for email content"""
    subject: str
    body: str

class DesignResponse(BaseModel):
    """Model for the complete design response including content and email"""
    content: PosterContent
    email: EmailContent

class PosterStyle(BaseModel):
    """Model for poster style configuration"""
    illustration_style: IllustrationStyle = IllustrationStyle.POSTER_DIGITAL
    size_format: ImageSize = ImageSize.SQUARE_HD
    colors: List[str] = []
    
    @property
    def image_size(self) -> Dict[str, int]:
        return self.size_format.get_dimensions()

class PosterService:
    def __init__(self):
        self.storage = RecraftStorage()
        
    async def generate_design_content(self, topic: str) -> DesignResponse:
        """Generate both design content and email content using OpenAI"""
        instructions = f"""
        Create a complete design package about {topic}, including both design specifications and email content.
        
        DESIGN SPECIFICATIONS:
        1. Create a powerful, attention-grabbing title
        2. Write a clear description of what the design should visually communicate
        3. Include a short, impactful text overlay (tagline or call to action)
        4. Choose the most appropriate visual style from these options:
           - POSTER_DIGITAL: Best for posters and marketing materials (2D art poster style)
           - LOGO_VECTOR: Best for logos and brand assets (clean vector art)
           - REALISTIC_PHOTO: Best for product mockups and realistic scenes
           - MODERN_MINIMAL: Best for clean, minimalist designs
           - NEON_FUTURISTIC: Best for tech and futuristic themes

        5. Choose the most appropriate size format based on the content:
           - SQUARE_HD: 1080x1080 - Best for high-detail square images (social media, logos)
           - SQUARE: 800x800 - Standard square format (avatars, thumbnails)
           - PORTRAIT_4_3: 1080x1440 - Portrait format for vertical designs
           - PORTRAIT_16_9: 1080x1920 - Tall portrait format (mobile, stories)
           - LANDSCAPE_4_3: 1440x1080 - Classic landscape format
           - LANDSCAPE_16_9: 1920x1080 - Widescreen landscape format (presentations)

        6. Suggest a color theme that reinforces the message
        7. Define the mood the design should convey
        8. List key visual elements that should be included
        9. Provide notes about the composition and layout

        EMAIL CONTENT:
        1. Create an engaging subject line that will grab attention
        2. Write a professional email body that includes:
           - Warm greeting
           - Brief introduction of the design
           - Key highlights and intended use
           - Any specific notes about the design choices
           - Professional closing
        
        Choose the visual style and size format that best match the topic and intended use.
        Make it visually striking and professional while maintaining clarity of message.
        Ensure all elements work together to create a cohesive design that effectively communicates the topic.
        """

        return await structured_openai_completion(
            instructions=instructions,
            original_content=topic,
            response_model=DesignResponse,
            temperature=0.7
        )

    async def create_design(
        self,
        topic: str,
        style: Optional[PosterStyle] = None,
        custom_prompt: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[EmailContent]]:
        """Create a design and return its URL and email content"""
        try:
            # Generate content if custom prompt is not provided
            if not custom_prompt:
                response = await self.generate_design_content(topic)
                content = response.content
                email = response.email
                
                # Create a shorter, focused prompt
                prompt = f"{content.title}. {content.text_overlay} {content.description[:200]}..."
                
                # Use the AI-selected style and size if not provided
                if not style:
                    style = PosterStyle(
                        illustration_style=content.visual_style,
                        size_format=content.size_format
                    )
            else:
                prompt = custom_prompt
                email = EmailContent(
                    subject=f"Your Design for {topic}",
                    body=f"Here's your custom design for {topic}.\n\nBest regards,\nDesign Team"
                )

            logger.info(f"Generating design with prompt: {prompt}")
            logger.info(f"Using style: {style.illustration_style.value}")
            logger.info(f"Using size format: {style.size_format.value} ({style.image_size})")
            
            # Convert hex colors to RGB dictionaries
            rgb_colors = []
            for color in style.colors:
                color = color.lstrip('#')
                rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
                rgb_colors.append({
                    "r": rgb[0],
                    "g": rgb[1],
                    "b": rgb[2]
                })
            
            # Submit to Recraft V3
            handler = await fal_client.submit_async(
                "fal-ai/recraft-v3",
                arguments={
                    "prompt": prompt,
                    "image_size": style.image_size,
                    "style": style.illustration_style.value,
                    "colors": rgb_colors
                }
            )

            # Log the generation progress
            async for event in handler.iter_events(with_logs=True):
                logger.info(f"Generation progress: {event}")

            # Get the final result
            result = await handler.get()
            
            if result and 'images' in result and len(result['images']) > 0:
                image_data = result['images'][0]
                
                # Store the image in Supabase
                logger.info(f"Storing generated image...")
                stored_url = await self.storage.store_recraft_image(image_data)
                
                if stored_url:
                    logger.info(f"Image stored successfully at: {stored_url}")
                    return stored_url, email
                else:
                    logger.error("Failed to store image in Supabase")
                    return None, None
            else:
                logger.error("Failed to generate image with Recraft V3")
                return None, None

        except Exception as e:
            logger.error(f"Error creating image: {str(e)}")
            return None, None

# Example test function
async def test_design_generation():
    service = PosterService()
    
    # Test cases with different topics
    test_cases = [
        {
            "topic": "Tech Startup Logo Design",
            "style": PosterStyle(
                size_format=ImageSize.SQUARE_HD,
                colors=["#4A90E2", "#50E3C2", "#B8E986"]
            )
        },
        {
            "topic": "Sustainable Product Packaging",
            "style": PosterStyle(
                size_format=ImageSize.LANDSCAPE_16_9,
                colors=["#2E7D32", "#1565C0", "#FDD835"]
            )
        },
        {
            "topic": "AI Conference 2024 Poster",
            "style": PosterStyle(
                size_format=ImageSize.PORTRAIT_16_9,
                colors=["#6200EA", "#00BFA5", "#FF1744"]
            )
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\nTest Case {i}:")
        logger.info(f"Topic: {test_case['topic']}")
        
        try:
            # Generate and send the design
            design_url, email = await service.create_design(
                topic=test_case['topic'],
                style=test_case['style']
            )
            
            if design_url:
                logger.info(f"✅ Success! Design {i} created and sent successfully")
                logger.info(f"URL: {design_url}")
            else:
                logger.error(f"❌ Failed to create design {i}")
                
        except Exception as e:
            logger.error(f"❌ Error in test case {i}: {str(e)}")
        
        # Add a small delay between tests
        await asyncio.sleep(2)

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the test
    asyncio.run(test_design_generation()) 