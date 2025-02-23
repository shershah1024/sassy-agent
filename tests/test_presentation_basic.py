import pytest
import os
from dotenv import load_dotenv
from presentation_service import PresentationService, SlideContent

# Load environment variables
load_dotenv()

@pytest.fixture
def presentation_service():
    return PresentationService()

@pytest.mark.asyncio
async def test_basic_presentation_creation(presentation_service):
    """Test creating a simple presentation with one slide"""
    slides = [
        SlideContent(
            layout="TITLE",
            title="Basic Test Presentation",
            subtitle="Testing Simple Creation"
        )
    ]
    
    presentation_id = await presentation_service.create_presentation(
        user_id="test_user",  # We'll use a test user ID
        title="Basic Test",
        slides=slides
    )
    
    assert presentation_id is not None
    assert isinstance(presentation_id, str)
    print(f"Created presentation with ID: {presentation_id}")

@pytest.mark.asyncio
async def test_presentation_with_content(presentation_service):
    """Test creating a presentation with text content"""
    slides = [
        SlideContent(
            layout="TITLE_AND_BODY",
            title="Content Test",
            content=["First bullet point", "Second bullet point", "Third bullet point"]
        )
    ]
    
    presentation_id = await presentation_service.create_presentation(
        user_id="test_user",
        title="Content Test",
        slides=slides
    )
    
    assert presentation_id is not None
    print(f"Created presentation with content, ID: {presentation_id}")

@pytest.mark.asyncio
async def test_presentation_with_image(presentation_service):
    """Test creating a presentation with an image"""
    slides = [
        SlideContent(
            layout="TITLE_AND_IMAGE",
            title="Image Test",
            images=["https://mbjkvwatoiryvmskgewn.supabase.co/storage/v1/object/public/igcse_spanish_images//generated_image_1740134345_3db63289.png"]
        )
    ]
    
    presentation_id = await presentation_service.create_presentation(
        user_id="test_user",
        title="Image Test",
        slides=slides
    )
    
    assert presentation_id is not None
    print(f"Created presentation with image, ID: {presentation_id}") 