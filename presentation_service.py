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
                client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
                scopes=[
                    'https://www.googleapis.com/auth/presentations',
                    'https://www.googleapis.com/auth/gmail.modify',  # Added Gmail scope
                    'https://www.googleapis.com/auth/gmail.send'     # Added Gmail send scope
                ]
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
                        content['leftContent'] = "Benefits:\n- Increased efficiency\n- Better accuracy\n- Cost reduction"
                        content['rightContent'] = "Challenges:\n- Implementation costs\n- Training requirements\n- Change management"
                    else:
                        # Ensure content is properly formatted for columns
                        content['leftContent'] = slide_content.content[0].replace('leftContent:', '').strip()
                        content['rightContent'] = slide_content.content[1].replace('rightContent:', '').strip()
                        logger.info(f"Two-column content: Left={content['leftContent']}, Right={content['rightContent']}")
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
            instructions = f"""
            Create a presentation structure about {topic} with exactly 7 slides.
            Each slide MUST have a clear, descriptive title that reflects its content.
            Make the content engaging and informative.

            SLIDE STRUCTURE (exactly in this order):
            1. Title slide (TITLE_GRADIENT layout) - with a compelling title and subtitle that captures the essence of {topic}
            2. Overview slide (BULLET_POINTS layout) - title should be "Overview" or similar, with 4-5 key points about the topic
            3. Image slide (IMAGE_CENTERED layout) - title should describe what the image will show, This is the ONLY slide that should have an image
            4. Two-column comparison slide (TWO_COLUMNS_EQUAL layout) - title should reflect the comparison being made
            5. Detailed analysis (TWO_COLUMNS_LEFT_WIDE layout) - title should indicate the analysis focus
            6. Key findings (NUMBER_POINTS layout) - title should be "Key Findings" or similar
            7. Summary slide (TITLE_LEFT layout) - title should be "Summary" or "Conclusion"

            For the image slide ONLY, provide a detailed image prompt in this format:
            "Professional photograph of [subject], [specific details], [style elements], [lighting], [composition]"

            For TWO_COLUMNS slides, provide content in this format:
            leftContent: [content for left column]
            rightContent: [content for right column]

            THEME SELECTION:
            Choose one of these themes based on the topic and content:
            - MIDNIGHT: Deep blue with modern accents (perfect for tech, space, or night-themed topics)
            - SUNSET: Modern gradient from purple to orange (great for creative or nature topics)
            - FOREST: Rich greens with earth tones (ideal for environmental or natural topics)
            - TECH: Modern tech-inspired theme (suited for technology and innovation topics)
            - MINIMAL: Clean, minimal design (professional and versatile)

            EMAIL CONTENT:
            Also generate a professional and engaging email to accompany the presentation:
            1. Subject line: Should be catchy and descriptive
            2. Body: Should include:
               - Warm greeting
               - Brief introduction of the presentation
               - Key highlights of what's included
               - Clear call-to-action to view the presentation
               - Professional closing with "Best regards, Shahir"
               Make it friendly but professional in tone.

            Return the slides array, selected theme name, and email content.
            """

            response = await structured_openai_completion(
                instructions=instructions,
                original_content=topic,
                response_model=PresentationStructure,
                temperature=0.7
            )

            slides = response.slides
            theme = response.theme if hasattr(response, 'theme') else "TECH"
            email_content = response.email if hasattr(response, 'email') else EmailContent(
                subject=f"Your Presentation: {slides[0].title if slides else 'New Presentation'} is Ready!",
                body=f"Your AI-generated presentation is ready to view.\n\nBest regards,\nShahir"
            )
            
            logger.info(f"Selected theme: {theme}")
            logger.info(f"Email subject: {email_content.subject}")
            
            # Ensure only the third slide (index 2) has an image
            for i, slide in enumerate(slides):
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

            return slides, theme, email_content

        except Exception as e:
            logger.error(f"Error generating presentation content: {str(e)}")
            return [], "TECH", EmailContent(
                subject="Your Presentation is Ready",
                body="Your AI-generated presentation is ready to view."
            )

    async def create_presentation_from_topic(
        self, 
        user_id: str, 
        title: str, 
        topic: str, 
        num_slides: int = 5,
        generate_images: bool = True,
        theme: str = "TECH"
    ) -> Optional[str]:
        """Create a presentation from a topic using AI-generated content"""
        try:
            # Generate content with image prompts
            slides, suggested_theme, email_content = await self.generate_presentation_content(topic, num_slides, generate_images=True)
            if not slides:
                return None

            # Use the AI-suggested theme unless explicitly overridden
            final_theme = theme if theme != "TECH" else suggested_theme
            logger.info(f"Using theme: {final_theme}")

            # Create presentation with the processed slides and theme
            return await self.create_presentation(user_id, title, slides, final_theme)

        except Exception as e:
            logger.error(f"Error creating presentation from topic: {str(e)}")
            return None 