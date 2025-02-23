import asyncio
from dotenv import load_dotenv
from presentation_service import PresentationService

# Load environment variables
load_dotenv()

# Use the specific user ID
USER_ID = "106573671377678694423"

async def test_ai_image_presentation():
    """Create a presentation about AI with automatically generated images"""
    print("\n=== Creating AI Presentation with Generated Images ===")
    service = PresentationService()
    
    # Create a presentation about AI and robotics to test image generation
    presentation_id = await service.create_presentation_from_topic(
        user_id=USER_ID,
        title="The Future of Robotics",
        topic="""Create a visually engaging presentation about modern robotics and automation.
                Include specific examples of robots in:
                - Manufacturing
                - Healthcare
                - Space exploration
                - Domestic use
                Make sure to describe the visual aspects clearly for AI image generation.""",
        num_slides=4,
        generate_images=True
    )
    
    print(f"Created presentation with ID: {presentation_id}")
    return presentation_id

async def main():
    """Run the test"""
    try:
        await test_ai_image_presentation()
    except Exception as e:
        print(f"Error running test: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 