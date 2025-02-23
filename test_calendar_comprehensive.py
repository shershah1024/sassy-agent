import asyncio
from token_service import TokenService
from google_services import GoogleServices
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_calendar_functions(user_id: str):
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
    created_calendars = []
    
    try:
        # 1. List existing calendars
        logger.info("\n1. Testing calendar listing...")
        calendars = google_services.list_calendars()
        logger.info(f"Found {len(calendars)} calendars")
        for calendar in calendars:
            logger.info(f"Calendar: {calendar['summary']} (ID: {calendar.get('id')})")

        # 2. Create a new calendar
        logger.info("\n2. Testing calendar creation...")
        new_calendar = google_services.create_calendar(
            summary="Test Calendar",
            description="A test calendar created by the test script"
        )
        created_calendars.append(new_calendar['id'])
        logger.info(f"Created new calendar: {new_calendar['id']}")

        # 3. Create a simple event (30 minutes from now)
        logger.info("\n3. Testing simple event creation...")
        now = datetime.utcnow()
        start_time = (now + timedelta(minutes=30)).isoformat() + 'Z'
        end_time = (now + timedelta(minutes=60)).isoformat() + 'Z'
        
        simple_event = google_services.create_calendar_event(
            summary="Test Simple Event",
            start_time=start_time,
            end_time=end_time,
            description="This is a test event with basic details"
        )
        created_events.append(simple_event['id'])
        logger.info(f"Created simple event: {simple_event['id']}")
        
        # 4. Get event details
        logger.info("\n4. Testing event details retrieval...")
        event_details = google_services.get_calendar_event(simple_event['id'])
        logger.info(f"Retrieved event details: {event_details['summary']}")
        
        # 5. Update event
        logger.info("\n5. Testing event update...")
        updated_event = google_services.update_calendar_event(
            event_id=simple_event['id'],
            summary="Updated Test Event",
            description="This event has been updated"
        )
        logger.info(f"Updated event summary: {updated_event['summary']}")
        
        # 6. Quick add event
        logger.info("\n6. Testing quick add event...")
        quick_event = google_services.quick_add_event("Meeting tomorrow at 3pm")
        created_events.append(quick_event['id'])
        logger.info(f"Created quick event: {quick_event['id']}")
        
        # 7. List events
        logger.info("\n7. Testing event listing...")
        events = google_services.list_calendar_events(
            max_results=5,
            time_min=now.isoformat() + 'Z',
            time_max=(now + timedelta(days=7)).isoformat() + 'Z'
        )
        logger.info(f"Found {len(events)} upcoming events")
        for event in events:
            logger.info(f"Event: {event['summary']} (ID: {event['id']})")
        
        # 8. Create event with attendees
        logger.info("\n8. Testing event creation with attendees...")
        start_time_2 = (now + timedelta(hours=1)).isoformat() + 'Z'
        end_time_2 = (now + timedelta(hours=2)).isoformat() + 'Z'
        
        event_with_attendees = google_services.create_calendar_event(
            summary="Test Event with Attendees",
            start_time=start_time_2,
            end_time=end_time_2,
            description="This is a test event with attendees",
            attendees=["test@example.com"]
        )
        created_events.append(event_with_attendees['id'])
        logger.info(f"Created event with attendees: {event_with_attendees['id']}")
        
        # Wait a moment before cleanup
        logger.info("\nWaiting for 2 seconds before cleanup...")
        await asyncio.sleep(2)
        
        # 9. Cleanup - Delete all created events
        logger.info("\n9. Testing event deletion...")
        for event_id in created_events:
            try:
                google_services.delete_calendar_event(event_id)
                logger.info(f"Successfully deleted event: {event_id}")
            except Exception as e:
                logger.error(f"Failed to delete event {event_id}: {str(e)}")
        
        # 10. Cleanup - Delete created calendar
        logger.info("\n10. Testing calendar deletion...")
        for calendar_id in created_calendars:
            try:
                google_services.delete_calendar(calendar_id)
                logger.info(f"Successfully deleted calendar: {calendar_id}")
            except Exception as e:
                logger.error(f"Failed to delete calendar {calendar_id}: {str(e)}")
        
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
        for calendar_id in created_calendars:
            try:
                google_services.delete_calendar(calendar_id)
                logger.info(f"Cleaned up calendar: {calendar_id}")
            except:
                pass

if __name__ == "__main__":
    USER_ID = "106573671377678694423"
    asyncio.run(test_calendar_functions(USER_ID)) 