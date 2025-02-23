from typing import List, Dict, Any, Optional
import os
import logging
from google.oauth2.credentials import Credentials
from presentation_generator import MultiStylePresentation, SlideType
from presentation_themes import THEMES
from token_service import TokenService
from openai_utils import structured_openai_completion
from image_service import ImageService
from image_storage import ImageStorage
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class SlideContent(BaseModel):
    """Model for slide content"""
    layout: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    content: Optional[List[str]] = None
    images: Optional[List[str]] = None
    imagePlaceholder: Optional[str] = None  # For AI image generation

class EmailContent(BaseModel):
    """Model for email content"""
    subject: str
    body: str

class PresentationService:
    def __init__(self):
        self.token_service = TokenService()
        self.image_service = ImageService()
        self.image_storage = ImageStorage()

    async def get_presentation_credentials(self, user_id: str) -> Optional[Credentials]:
        """Get valid Google credentials for presentations"""
        try:
            access_token = await self.token_service.get_valid_token(user_id)
            if not access_token:
                logger.error(f"No valid token found for user {user_id}")
                return None

            credentials = Credentials(
                token=access_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=os.getenv('GOOGLE_CLIENT_ID'),
                client_secret=os.getenv('GOOGLE_CLIENT_SECRET')
            )
            return credentials
        except Exception as e:
            logger.error(f"Error getting credentials: {str(e)}")
            return None

    async def create_presentation(self, user_id: str, title: str, slides: List[SlideContent], theme: str = "TECH") -> Optional[str]:
        """Create a new presentation with the given title and slides"""
        try:
            # Get credentials
            credentials = await self.get_presentation_credentials(user_id)
            if not credentials:
                return None

            # Initialize presentation service
            presentation = MultiStylePresentation(credentials)
            
            # Create presentation with theme
            presentation_id = presentation.create_presentation(title, theme)
            logger.info(f"Created presentation with ID: {presentation_id}")

            # Process slides and generate images if needed
            for i, slide_content in enumerate(slides):
                logger.info(f"\nProcessing slide {i + 1}:")
                logger.info(f"Slide layout: {slide_content.layout}")
                logger.info(f"Slide title: {slide_content.title}")
                logger.info(f"Slide content: {slide_content.content}")
                
                # Check if we need to generate an image
                if slide_content.imagePlaceholder:
                    logger.info(f"Generating image for prompt: {slide_content.imagePlaceholder}")
                    fal_result = await self.image_service.generate_image(slide_content.imagePlaceholder)
                    logger.info(f"FAL result: {fal_result}")
                    if fal_result and 'url' in fal_result:
                        # Store the FAL AI image in Supabase
                        logger.info("Storing image in Supabase...")
                        stored_url = await self.image_storage.store_image_from_url(fal_result['url'])
                        if stored_url:
                            logger.info(f"Image stored successfully at: {stored_url}")
                            slide_content.images = [stored_url]
                            logger.info(f"Updated slide_content.images: {slide_content.images}")
                        else:
                            logger.error("Failed to store image in Supabase")
                    slide_content.imagePlaceholder = None

                # Convert layout to SlideType
                try:
                    slide_type = SlideType[slide_content.layout]
                    logger.info(f"Converted layout to SlideType: {slide_type}")
                except (KeyError, ValueError):
                    logger.warning(f"Unknown layout type: {slide_content.layout}, defaulting to TITLE_CENTERED")
                    slide_type = SlideType.TITLE_CENTERED

                # Prepare slide content with defaults
                content = {
                    'title': slide_content.title or "Untitled Slide",  # Ensure title is never None
                    'subtitle': slide_content.subtitle or "",  # Empty string if no subtitle
                }

                # Handle different slide types
                if slide_type in [SlideType.BULLET_POINTS, SlideType.NUMBER_POINTS]:
                    content['points'] = slide_content.content or ["No points provided"]
                elif slide_type in [SlideType.TWO_COLUMNS_EQUAL, SlideType.TWO_COLUMNS_LEFT_WIDE, SlideType.TWO_COLUMNS_RIGHT_WIDE]:
                    # For two-column slides, content should be a list with exactly two items
                    # First item is left column content, second item is right column content
                    if not slide_content.content or len(slide_content.content) < 2:
                        logger.warning(f"Insufficient content for two-column slide {i + 1}")
                        content['leftContent'] = "No content provided for left column"
                        content['rightContent'] = "No content provided for right column"
                    else:
                        # Process each column's content
                        left_content = ""
                        right_content = ""
                        
                        for item in slide_content.content:
                            if "leftContent:" in item:
                                left_content = item.replace('leftContent:', '').strip()
                            elif "rightContent:" in item:
                                right_content = item.replace('rightContent:', '').strip()
                        
                        # If no explicit left/right content found, use first two items
                        if not left_content and not right_content and len(slide_content.content) >= 2:
                            left_content = slide_content.content[0]
                            right_content = slide_content.content[1]
                        
                        content['leftContent'] = left_content or "No content provided for left column"
                        content['rightContent'] = right_content or "No content provided for right column"
                        
                        logger.info(f"Two-column content processed - Left: {content['leftContent'][:50]}..., Right: {content['rightContent'][:50]}...")
                elif slide_type == SlideType.IMAGE_CENTERED:
                    if slide_content.images:
                        content['imageUrl'] = slide_content.images[0]
                        logger.info(f"Added image URL to content: {content['imageUrl']}")
                    content['text'] = "\n".join(slide_content.content) if slide_content.content else ""
                else:
                    # For all other slide types, join content as text if available
                    content['text'] = "\n".join(slide_content.content) if slide_content.content else ""

                # Add slide with content
                logger.info(f"Adding slide with content: {content}")
                slide_id = presentation.add_slide(presentation_id, slide_type, content, insertion_index=i)
                if not slide_id:
                    logger.error(f"Failed to add slide {i}")
                    continue
                logger.info(f"Successfully added slide with ID: {slide_id}")

            return presentation_id

        except Exception as e:
            logger.error(f"Error creating presentation: {str(e)}")
            return None

    async def generate_presentation_content(self, topic: str, num_slides: int = 5, generate_images: bool = False) -> tuple[List[SlideContent], str, EmailContent]:
        """Generate presentation content using OpenAI"""
        class PresentationStructure(BaseModel):
            slides: List[SlideContent]
            theme: str
            email: EmailContent

        try:
            instructions = f"""Create a compelling {num_slides}-slide presentation about {topic}.

For each slide, provide:
1. A clear, engaging title
2. The appropriate slide layout type from these options:
   - TITLE: Opening slide with title and subtitle
   - SECTION: Section header with title
   - BULLETS: Bullet points
   - TWO_COLUMNS_EQUAL: Two equal columns
   - TWO_COLUMNS_LEFT_WIDE: Two columns with wider left column
   - TWO_COLUMNS_RIGHT_WIDE: Two columns with wider right column
   - IMAGE_CENTERED: Centered image with optional caption
   - QUOTE: Featured quote
   - CLOSING: Closing slide

3. Content appropriate for the layout:
   - For TITLE slides: Include a subtitle
   - For SECTION slides: Just the title is sufficient
   - For BULLETS: List 3-5 key points
   - For TWO_COLUMNS slides: MUST provide content in this format:
     ["leftContent: [Your left column content here]", "rightContent: [Your right column content here]"]
   - For IMAGE_CENTERED: Provide an image description or placeholder
   - For QUOTE: Provide the quote and attribution
   - For CLOSING: Include a summary or call to action

4. For image slides, provide a clear description of what the image should show.

IMPORTANT RULES:
1. For TWO_COLUMNS slides, you MUST provide exactly two items in the content array:
   - First item must start with "leftContent:" followed by the content
   - Second item must start with "rightContent:" followed by the content
2. Never leave content empty for any slide type
3. For SECTION slides, include 1-2 key points in the content array
4. For BULLETS slides, always provide 3-5 bullet points

Also suggest:
1. A presentation theme from these options: MIDNIGHT, SUNSET, FOREST, TECH, MINIMAL
2. A professional email to accompany the presentation

Make the content engaging, professional, and well-structured.
Ensure smooth transitions between slides and a clear narrative flow.
"""

            response = await structured_openai_completion(
                instructions=instructions,
                original_content=topic,
                response_model=PresentationStructure,
                temperature=0.7
            )

            slides = response.slides
            # Ensure we use a valid theme
            theme = response.theme.upper() if hasattr(response, 'theme') else "TECH"
            if theme not in ["MIDNIGHT", "SUNSET", "FOREST", "TECH", "MINIMAL"]:
                logger.warning(f"Invalid theme {theme}, defaulting to TECH")
                theme = "TECH"
            
            email_content = response.email if hasattr(response, 'email') else EmailContent(
                subject=f"Your Presentation: {slides[0].title if slides else 'New Presentation'} is Ready!",
                body=f"Your AI-generated presentation is ready to view.\n\nBest regards,\nShahir"
            )
            
            logger.info(f"Using theme: {theme}")
            logger.info(f"Email subject: {email_content.subject}")
            
            # Ensure only the third slide (index 2) has an image
            for i, slide in enumerate(slides):
                # Ensure SECTION slides have content
                if slide.layout == "SECTION" and not slide.content:
                    slide.content = [slide.title]
                
                # Ensure TWO_COLUMNS slides have proper content
                if slide.layout in ["TWO_COLUMNS_EQUAL", "TWO_COLUMNS_LEFT_WIDE", "TWO_COLUMNS_RIGHT_WIDE"]:
                    if not slide.content or len(slide.content) < 2:
                        slide.content = [
                            f"leftContent: Key points about {slide.title}",
                            f"rightContent: Details about {slide.title}"
                        ]
                
                if i == 2:  # Third slide
                    if not slide.imagePlaceholder and not slide.images:
                        # Generate image prompt if not provided
                        prompt_content = f"{slide.title}"
                        if slide.content:
                            prompt_content += f" showing {', '.join(slide.content[:2])}"
                        image_prompt = f"Professional visualization of {prompt_content}, modern style, high quality, photorealistic"
                        
                        # Generate the image using FAL AI
                        logger.info(f"Generating image with prompt: {image_prompt}")
                        fal_result = await self.image_service.generate_image(image_prompt)
                        
                        if fal_result and 'url' in fal_result:
                            # Store the image in Supabase
                            logger.info("Storing image in Supabase...")
                            stored_url = await self.image_storage.store_image_from_url(fal_result['url'])
                            if stored_url:
                                logger.info(f"Image stored successfully at: {stored_url}")
                                slide.images = [stored_url]
                            else:
                                logger.error("Failed to store image in Supabase")
                        else:
                            logger.error("Failed to generate image with FAL AI")
                    
                    slide.layout = "IMAGE_CENTERED"
                else:
                    # Remove any image placeholders from other slides
                    slide.imagePlaceholder = None
                    slide.images = None

            if not slides:
                raise ValueError("Failed to generate presentation content: No slides were created")
                
            return slides, theme, email_content

        except Exception as e:
            logger.error(f"Error generating presentation content: {str(e)}")
            raise ValueError(f"Failed to generate presentation content: {str(e)}")

    async def create_presentation_from_topic(
        self, 
        user_id: str, 
        title: str, 
        topic: str, 
        num_slides: int = 5,
        generate_images: bool = True,
        theme: str = "TECH"
    ) -> str:
        """Create a presentation from a topic using AI-generated content"""
        try:
            # Generate content with image prompts
            slides, suggested_theme, email_content = await self.generate_presentation_content(topic, num_slides, generate_images=True)
            
            # Use the AI-suggested theme unless explicitly overridden
            final_theme = theme if theme != "TECH" else suggested_theme
            logger.info(f"Using theme: {final_theme}")

            # Create presentation with the processed slides and theme
            presentation_id = await self.create_presentation(user_id, title, slides, final_theme)
            if not presentation_id:
                raise ValueError("Failed to create presentation: No presentation ID returned")
                
            return presentation_id

        except Exception as e:
            logger.error(f"Error creating presentation from topic: {str(e)}")
            raise ValueError(f"Failed to create presentation: {str(e)}") 