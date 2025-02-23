import pytest
from dotenv import load_dotenv
from presentation_service import PresentationService, SlideContent

# Load environment variables
load_dotenv()

@pytest.fixture
def presentation_service():
    return PresentationService()

@pytest.mark.asyncio
async def test_ai_content_generation(presentation_service):
    """Test generating presentation content using AI"""
    slides = await presentation_service.generate_presentation_content(
        topic="The Future of Artificial Intelligence",
        num_slides=3
    )
    
    assert slides is not None
    assert len(slides) == 3
    assert all(isinstance(slide, SlideContent) for slide in slides)
    
    # Print generated content for inspection
    print("\nGenerated AI Content:")
    for i, slide in enumerate(slides, 1):
        print(f"\nSlide {i}:")
        print(f"Title: {slide.title}")
        if slide.subtitle:
            print(f"Subtitle: {slide.subtitle}")
        if slide.content:
            print("Content:")
            for point in slide.content:
                print(f"- {point}")

@pytest.mark.asyncio
async def test_full_ai_presentation_creation(presentation_service):
    """Test creating a complete presentation from an AI-generated topic"""
    presentation_id = await presentation_service.create_presentation_from_topic(
        user_id="test_user",
        title="AI in Healthcare",
        topic="How Artificial Intelligence is Transforming Healthcare",
        num_slides=4
    )
    
    assert presentation_id is not None
    print(f"\nCreated AI-generated presentation with ID: {presentation_id}")

@pytest.mark.asyncio
async def test_ai_presentation_with_specific_format(presentation_service):
    """Test generating a presentation with a specific format requirement"""
    instructions = """
    Create a presentation about 'Climate Change Solutions' with the following structure:
    1. Problem Overview
    2. Current Impact
    3. Technological Solutions
    4. Call to Action
    """
    
    slides = await presentation_service.generate_presentation_content(
        topic=instructions,
        num_slides=4
    )
    
    assert slides is not None
    assert len(slides) == 4
    
    # Create the presentation with the generated content
    presentation_id = await presentation_service.create_presentation(
        user_id="test_user",
        title="Climate Change Solutions",
        slides=slides
    )
    
    assert presentation_id is not None
    print(f"\nCreated structured AI presentation with ID: {presentation_id}") 