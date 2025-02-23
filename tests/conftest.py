import pytest
import os
from dotenv import load_dotenv

# Load environment variables before any tests run
@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv()
    # Verify required environment variables
    required_vars = [
        'GOOGLE_CLIENT_ID',
        'GOOGLE_CLIENT_SECRET',
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'azure_text_endpoint',
        'azure_text_api_key',
        'azure_text_api_version'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        pytest.fail(f"Missing required environment variables: {', '.join(missing)}")

# Add any other shared fixtures here
@pytest.fixture(scope="session")
def test_user_id():
    """Provide a consistent test user ID across tests"""
    return "test_user_123" 