import asyncio
import logging
from google_api_wrapper import create_image_and_send_email
from poster_service import PosterStyle, IllustrationStyle, ImageSize

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test user ID
TEST_USER_ID = "107085158246892440905"  # Replace with actual test user ID

async def test_poster_email_generation():
    """Test the poster generation and email sending functionality"""
    
    # Test cases with different topics and instructions
    test_cases = [
        {
            "instructions": "Create an environmental awareness poster about ocean conservation with vibrant colors and marine life",
            "email": "test@example.com"
        },
        {
            "instructions": "Design a modern tech startup poster highlighting artificial intelligence and innovation",
            "email": "test@example.com"
        },
        {
            "instructions": "Generate a health and wellness poster about mindfulness and meditation",
            "email": "test@example.com"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\nTest Case {i}:")
        logger.info(f"Instructions: {test_case['instructions']}")
        
        try:
            # Generate poster and send email
            result = await create_image_and_send_email(
                user_id=TEST_USER_ID,
                instructions=test_case["instructions"],
                recipient_email=test_case["email"]
            )
            
            if result["status"] == "success":
                logger.info(f"✅ Success! Poster {i} created and email sent")
                logger.info(f"Image URL: {result['image_url']}")
                logger.info(f"Message: {result['message']}")
            else:
                logger.error(f"❌ Failed to create poster {i}")
                logger.error(f"Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"❌ Error in test case {i}: {str(e)}")
        
        # Add a small delay between tests
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(test_poster_email_generation()) 