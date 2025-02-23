import asyncio
from token_service import TokenService
from google_services import GoogleServices
from datetime import datetime, timedelta

async def test_calendar_functions(user_id: str):
    # Initialize token service
    token_service = TokenService()
    
    # Get valid token for the user
    token = await token_service.get_valid_token(user_id)
    if not token:
        print("Could not get valid token for the user")
        return
    
    # Initialize Google Services with the token
    google_services = GoogleServices(token)
    
    # Create a test event (30 minutes from now)
    now = datetime.utcnow()
    start_time = (now + timedelta(minutes=30)).isoformat() + 'Z'  # 'Z' indicates UTC
    end_time = (now + timedelta(minutes=60)).isoformat() + 'Z'
    
    try:
        # Create a calendar event
        print("Creating calendar event...")
        event = google_services.create_calendar_event(
            summary="Test Calendar Event",
            start_time=start_time,
            end_time=end_time,
            description="This is a test event created by the calendar function test script"
        )
        print(f"Created event: {event}")
        
        # Wait for a moment
        await asyncio.sleep(2)
        
        # Delete the event
        print(f"\nDeleting event with ID: {event['id']}")
        google_services.delete_calendar_event(event['id'])
        print("Event deleted successfully")
        
    except Exception as e:
        print(f"Error during calendar operations: {str(e)}")

if __name__ == "__main__":
    USER_ID = "106573671377678694423"
    asyncio.run(test_calendar_functions(USER_ID)) 