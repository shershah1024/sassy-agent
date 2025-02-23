import asyncio
import logging
from presentation_service import PresentationService
from presentation_themes import SlideType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use the specific user ID
USER_ID = "107085158246892440905"

async def test_presentation_with_images():
    """Create a presentation about space exploration with the MIDNIGHT theme"""
    service = PresentationService()
    
    logger.info("Creating presentation about space exploration...")
    
    presentation_id = await service.create_presentation_from_topic(
        user_id=USER_ID,
        title="Space: The Final Frontier",
        topic="""Create an awe-inspiring presentation about space exploration:
                - Title slide showcasing the vastness of space
                - Latest achievements in space exploration
                - Future missions and possibilities
                
                For the title image, create a photorealistic, high-quality image of:
                "A breathtaking view of Earth from space, with the International Space Station 
                silhouetted against the blue marble of our planet, stars visible in the 
                background, dramatic lighting from the sun creating a golden halo effect 
                around Earth's atmosphere. Professional space photography style with 
                perfect exposure and composition."
                """,
        num_slides=3,
        generate_images=True,
        theme="MIDNIGHT"  # Using the MIDNIGHT theme for space content
    )
    
    if presentation_id:
        logger.info(f"Successfully created presentation: {presentation_id}")
        logger.info("You can view it at: https://docs.google.com/presentation/d/" + presentation_id)
    else:
        logger.error("Failed to create presentation")

if __name__ == "__main__":
    asyncio.run(test_presentation_with_images()) 