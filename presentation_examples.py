import asyncio
from dotenv import load_dotenv
from presentation_service import PresentationService, SlideContent
from image_service import ImageService

# Load environment variables
load_dotenv()

# Use the specific user ID
USER_ID = "106573671377678694423"

async def example_1_basic_presentation():
    """Create a simple presentation with one slide"""
    print("\n=== Example 1: Basic Presentation ===")
    service = PresentationService()
    image_service = ImageService()
    
    # Generate an image first
    image_url = await image_service.generate_image(
        "A beautiful sunrise over a modern city skyline, professional photography"
    )
    
    slides = [
        SlideContent(
            layout="TITLE",
            title="My First Presentation",
            subtitle="Created with Python"
        ),
        SlideContent(
            layout="IMAGE_CENTERED",
            title="AI Generated Image",
            images=[image_url] if image_url else []
        )
    ]
    
    presentation_id = await service.create_presentation(
        user_id=USER_ID,
        title="Basic Example with AI Image",
        slides=slides
    )
    
    print(f"Created presentation with ID: {presentation_id}")
    return presentation_id

async def example_2_presentation_with_content():
    """Create a presentation with multiple slides and content"""
    print("\n=== Example 2: Presentation with Content and Images ===")
    service = PresentationService()
    image_service = ImageService()
    
    # Generate images for our slides
    tech_image = await image_service.generate_image(
        "Futuristic technology visualization, holographic interface"
    )
    nature_image = await image_service.generate_image(
        "Pristine natural landscape with mountains and forest"
    )
    
    slides = [
        SlideContent(
            layout="TITLE",
            title="Multi-Slide Presentation",
            subtitle="With Different Content Types"
        ),
        SlideContent(
            layout="TITLE_AND_BODY",
            title="Bullet Points",
            content=[
                "First important point",
                "Second crucial point",
                "Final takeaway"
            ]
        ),
        SlideContent(
            layout="IMAGE_CENTERED",
            title="Technology Today",
            images=[tech_image] if tech_image else []
        ),
        SlideContent(
            layout="IMAGE_CENTERED",
            title="Nature's Beauty",
            images=[nature_image] if nature_image else []
        )
    ]
    
    presentation_id = await service.create_presentation(
        user_id=USER_ID,
        title="Content Example with AI Images",
        slides=slides
    )
    
    print(f"Created presentation with ID: {presentation_id}")
    return presentation_id

async def example_3_ai_generated_presentation():
    """Create a presentation using AI-generated content and images"""
    print("\n=== Example 3: AI-Generated Presentation with Images ===")
    service = PresentationService()
    
    presentation_id = await service.create_presentation_from_topic(
        user_id=USER_ID,
        title="Future of Technology",
        topic="The impact of artificial intelligence and machine learning on society in the next decade, including relevant AI-generated images",
        num_slides=5,
        generate_images=True  # Enable image generation
    )
    
    print(f"Created AI-generated presentation with ID: {presentation_id}")
    return presentation_id

async def main():
    """Run all examples"""
    try:
        # Example 1: Basic presentation with image
        await example_1_basic_presentation()
        
        # Example 2: Presentation with content and images
        await example_2_presentation_with_content()
        
        # Example 3: AI-generated presentation with images
        await example_3_ai_generated_presentation()
        
    except Exception as e:
        print(f"Error running examples: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 