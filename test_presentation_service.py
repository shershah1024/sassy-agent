import pytest
import os
from dotenv import load_dotenv
from presentation_service import PresentationService, SlideContent

# Load environment variables
load_dotenv()

@pytest.fixture
def presentation_service():
    return PresentationService()

@pytest.fixture
def sample_slides():
    return [
        SlideContent(
            layout="TITLE",
            title="Test Presentation",
            subtitle="Created with Python"
        ),
        SlideContent(
            layout="TITLE_AND_BODY",
            title="Slide 1",
            content=["This is a test slide", "With multiple bullet points"]
        ),
        SlideContent(
            layout="TITLE_AND_TWO_COLUMNS",
            title="Slide 2",
            content=["Left column content", "Right column content"],
            images=["https://example.com/test.jpg"]
        )
    ]

@pytest.mark.asyncio
async def test_create_presentation(presentation_service, sample_slides):
    # Get test user ID from environment
    user_id = os.getenv("TEST_USER_ID")
    assert user_id is not None, "TEST_USER_ID environment variable is required"

    # Create presentation
    presentation_id = await presentation_service.create_presentation(
        user_id=user_id,
        title="Test Presentation",
        slides=sample_slides
    )

    assert presentation_id is not None
    assert isinstance(presentation_id, str)

@pytest.mark.asyncio
async def test_generate_presentation_content(presentation_service):
    # Generate content
    slides = await presentation_service.generate_presentation_content(
        topic="Artificial Intelligence",
        num_slides=3
    )

    assert slides is not None
    assert len(slides) == 3
    assert all(isinstance(slide, SlideContent) for slide in slides)

@pytest.mark.asyncio
async def test_create_presentation_from_topic(presentation_service):
    # Get test user ID from environment
    user_id = os.getenv("TEST_USER_ID")
    assert user_id is not None, "TEST_USER_ID environment variable is required"

    # Create presentation from topic
    presentation_id = await presentation_service.create_presentation_from_topic(
        user_id=user_id,
        title="AI Overview",
        topic="Artificial Intelligence",
        num_slides=3
    )

    assert presentation_id is not None
    assert isinstance(presentation_id, str)

@pytest.mark.asyncio
async def test_invalid_user_id(presentation_service, sample_slides):
    # Test with invalid user ID
    presentation_id = await presentation_service.create_presentation(
        user_id="invalid_user_id",
        title="Test Presentation",
        slides=sample_slides
    )

    assert presentation_id is None 