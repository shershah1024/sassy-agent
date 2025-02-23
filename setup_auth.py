from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
import asyncio
from token_service import TokenService
from datetime import datetime, timedelta

# Define all required scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',  # View and edit events on all calendars
    'https://www.googleapis.com/auth/calendar.app.created',  # Make secondary calendars and manage events
    'https://www.googleapis.com/auth/drive.file',  # Access to specific Drive files
    'https://www.googleapis.com/auth/presentations',  # Full access to Slides
    'https://www.googleapis.com/auth/gmail.modify',  # Read, compose, and send emails
    'https://www.googleapis.com/auth/documents'  # Access to Docs
]

async def setup_auth(user_id: str):
    token_service = TokenService()
    
    # Check if credentials.json exists
    if not os.path.exists('credentials.json'):
        raise FileNotFoundError(
            "credentials.json not found. Please download it from Google Cloud Console "
            "and place it in the project root directory."
        )
    
    # Start OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Calculate expiry timestamp
    expires_at = int((datetime.utcnow() + timedelta(seconds=creds.expiry.timestamp() - datetime.now().timestamp())).timestamp())
    
    # Save to Supabase
    success = await token_service.save_token(
        user_id=user_id,
        access_token=creds.token,
        refresh_token=creds.refresh_token,
        expires_at=expires_at,
        provider='google'
    )
    
    if success:
        print(f"Successfully saved new token for user {user_id}")
        print("You can now run the calendar tests!")
    else:
        print(f"Failed to save token for user {user_id}")

if __name__ == "__main__":
    USER_ID = "106573671377678694423"
    asyncio.run(setup_auth(USER_ID)) 