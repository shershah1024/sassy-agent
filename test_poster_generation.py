import asyncio
import logging
from presentation_service import PresentationService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_poster_generation():
    service = PresentationService()
    
    # Test cases with different topics and styles
    test_cases = [
        {
            "topic": "Artificial Intelligence in Healthcare",
            "style": "modern minimalist with medical theme",
            "size": "1080x1920"
        },
        {
            "topic": "Climate Change Action",
            "style": "nature-inspired with bold typography",
            "size": "1080x1920"
        },
        {
            "topic": "Digital Privacy in 2024",
            "style": "cyberpunk with tech elements",
            "size": "1080x1920"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\nTest Case {i}:")
        logger.info(f"Topic: {test_case['topic']}")
        logger.info(f"Style: {test_case['style']}")
        
        try:
            poster_url = await service.create_poster(
                topic=test_case['topic'],
                style=test_case['style'],
                size=test_case['size']
            )
            
            if poster_url:
                logger.info(f"✅ Success! Poster {i} created successfully")
                logger.info(f"URL: {poster_url}")
            else:
                logger.error(f"❌ Failed to create poster {i}")
                
        except Exception as e:
            logger.error(f"❌ Error in test case {i}: {str(e)}")
        
        # Add a small delay between tests
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(test_poster_generation()) 