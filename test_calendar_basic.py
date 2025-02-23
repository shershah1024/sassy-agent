import asyncio
from token_service import TokenService
from google_services import GoogleServices
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_calendar_functions(user_id: str):
    # Initialize token service
    token_service = TokenService()
    
    # Get valid token for the user
    logger.info(f"Getting token for user {user_id}")
    token = await token_service.get_valid_token(user_id)
    if not token:
        logger.error("Could not get valid token for the user")
        return
    
    # Initialize Google Services with the token
    google_services = GoogleServices(token)
    created_events = []
    
    try:
        # 1. Create a simple event (30 minutes from now)
        logger.info("\n1. Testing simple event creation...")
        now = datetime.utcnow()
        start_time = (now + timedelta(minutes=30)).isoformat() + 'Z'
        end_time = (now + timedelta(minutes=60)).isoformat() + 'Z'
        
        event = google_services.create_calendar_event(
            summary="Test Event",
            start_time=start_time,
            end_time=end_time,
            description="This is a test event"
        )
        created_events.append(event['id'])
        logger.info(f"Created event: {event['id']}")
        
        # 2. Create a recurring event (weekly for 4 weeks)
        logger.info("\n2. Testing recurring event creation...")
        start_time_recurring = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0).isoformat() + 'Z'
        end_time_recurring = (now + timedelta(days=1)).replace(hour=11, minute=0, second=0).isoformat() + 'Z'
        
        recurring_event = google_services.create_calendar_event(
            summary="Weekly Team Meeting",
            start_time=start_time_recurring,
            end_time=end_time_recurring,
            description="Recurring team sync-up meeting",
            recurrence=["RRULE:FREQ=WEEKLY;COUNT=4"]  # Repeat weekly for 4 weeks
        )
        created_events.append(recurring_event['id'])
        logger.info(f"Created recurring event: {recurring_event['id']}")
        
        # 3. View upcoming events
        logger.info("\n3. Testing event listing...")
        # List events for the next 30 days
        upcoming_events = google_services.list_calendar_events(
            time_min=now.isoformat() + 'Z',
            time_max=(now + timedelta(days=30)).isoformat() + 'Z'
        )
        logger.info(f"Found {len(upcoming_events)} upcoming events:")
        for evt in upcoming_events:
            logger.info(f"- {evt['summary']} ({evt.get('start', {}).get('dateTime', 'No date')})")
            if evt.get('recurrence'):
                logger.info(f"  Recurrence rule: {evt['recurrence']}")
        
        # 4. Get specific event details
        logger.info("\n4. Testing event retrieval...")
        event_details = google_services.get_calendar_event(event['id'])
        logger.info(f"Retrieved event summary: {event_details['summary']}")
        
        # 5. Update event
        logger.info("\n5. Testing event update...")
        updated_event = google_services.update_calendar_event(
            event_id=event['id'],
            summary="Updated Test Event",
            description="This event has been updated"
        )
        logger.info(f"Updated event summary: {updated_event['summary']}")
        
        # Wait a moment before deletion
        logger.info("\nWaiting for 2 seconds before deletion...")
        await asyncio.sleep(2)
        
        # 6. Delete events
        logger.info("\n6. Testing event deletion...")
        for event_id in created_events:
            google_services.delete_calendar_event(event_id)
            logger.info(f"Successfully deleted event: {event_id}")
        
        logger.info("\nAll calendar tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during calendar operations: {str(e)}")
        
        # Attempt cleanup on error
        logger.info("\nAttempting cleanup after error...")
        for event_id in created_events:
            try:
                google_services.delete_calendar_event(event_id)
                logger.info(f"Cleaned up event: {event_id}")
            except:
                pass

if __name__ == "__main__":
    USER_ID = "106573671377678694423"
    asyncio.run(test_basic_calendar_functions(USER_ID)) 