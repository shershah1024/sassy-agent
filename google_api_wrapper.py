from typing import Optional, List, Dict, Any
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import base64
import os
from presentation_service import PresentationService

logger = logging.getLogger(__name__)

# Constants
DEFAULT_RECIPIENT_EMAIL = "abdul.shahir@gmail.com"

# Email Functions
async def send_email(
    user_id: str, 
    instructions: str, 
    recipient_email: str = DEFAULT_RECIPIENT_EMAIL,
    subject: str = None,
    body: str = None
) -> Dict[str, Any]:
    """
    Send an email using Gmail API based on instructions
    
    Args:
        user_id: The user's ID for authentication
        instructions: Natural language instructions for the email content
        recipient_email: Email address of the recipient (defaults to DEFAULT_RECIPIENT_EMAIL)
        subject: Email subject line (optional)
        body: Email body content (optional)
    
    Returns:
        Dict[str, Any]: Response from Gmail API
    """
    try:
        service = PresentationService()
        credentials = await service.get_presentation_credentials(user_id)
        if not credentials:
            raise ValueError("Invalid credentials")

        # If subject/body not provided, use instructions as body and first line as subject
        if subject is None:
            subject = instructions.split('\n')[0]
        if body is None:
            body = instructions
        
        # Build Gmail service with correct scope
        gmail_service = build('gmail', 'v1', credentials=credentials)
        
        # Get user's email address for the 'from' field
        user_profile = gmail_service.users().getProfile(userId='me').execute()
        sender_email = user_profile['emailAddress']
        
        message = {
            'raw': _create_message(sender_email, recipient_email, subject, body)
        }
        
        # Send the email
        result = gmail_service.users().messages().send(userId='me', body=message).execute()
        logger.info(f"Email sent successfully to {recipient_email}")
        logger.info(f"Message ID: {result.get('id')}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise

def read_emails(user_id: str, instructions: str) -> List[Dict[str, Any]]:
    """Read emails based on instructions"""
    try:
        service = PresentationService()
        credentials = service.get_presentation_credentials(user_id)
        if not credentials:
            raise ValueError("Invalid credentials")

        # Parse instructions to get filters and criteria
        gmail_service = build('gmail', 'v1', credentials=credentials)
        messages = gmail_service.users().messages().list(userId='me').execute()
        
        emails = []
        for msg in messages.get('messages', []):
            email = gmail_service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = email.get('payload', {}).get('headers', [])
            emails.append({
                'id': email['id'],
                'subject': next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No subject'),
                'from': next((h['value'] for h in headers if h['name'].lower() == 'from'), 'No sender'),
                'snippet': email.get('snippet', '')
            })
        return emails
    except Exception as e:
        logger.error(f"Error reading emails: {str(e)}")
        raise

# Calendar Functions
async def create_event(user_id: str, instructions: str) -> Dict[str, Any]:
    """Create a calendar event based on instructions"""
    try:
        service = PresentationService()
        credentials = await service.get_presentation_credentials(user_id)
        if not credentials:
            raise ValueError("Invalid credentials")

        # Parse instructions to get event details using AI
        calendar_service = build('calendar', 'v3', credentials=credentials)
        
        # AI would extract these details from instructions
        event = {
            'summary': 'Event from instructions',
            'start': {'dateTime': '2024-03-20T09:00:00Z', 'timeZone': 'UTC'},
            'end': {'dateTime': '2024-03-20T10:00:00Z', 'timeZone': 'UTC'},
        }
        
        return calendar_service.events().insert(calendarId='primary', body=event).execute()
    except Exception as e:
        logger.error(f"Error creating event: {str(e)}")
        raise

async def list_events(user_id: str, instructions: str) -> List[Dict[str, Any]]:
    """List calendar events based on instructions"""
    try:
        service = PresentationService()
        credentials = await service.get_presentation_credentials(user_id)
        if not credentials:
            raise ValueError("Invalid credentials")

        calendar_service = build('calendar', 'v3', credentials=credentials)
        
        # AI would parse instructions to determine time range and filters
        events_result = calendar_service.events().list(
            calendarId='primary',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])
    except Exception as e:
        logger.error(f"Error listing events: {str(e)}")
        raise

# Presentation Function
async def create_presentation(user_id: str, instructions: str) -> str:
    """
    Create a complete presentation based on instructions and send an email with the link.
    
    Args:
        user_id: The user's ID for authentication
        instructions: Natural language instructions for the presentation
    
    Returns:
        str: Complete Google Slides URL
    """
    try:
        service = PresentationService()
        
        # Extract title from instructions (first line or main topic)
        title = instructions.split('\n')[0].strip()
        
        # First, get the AI-generated content to determine the theme
        slides, suggested_theme, email_content = await service.generate_presentation_content(
            topic=instructions,
            num_slides=7,  # We want exactly 7 slides as per requirements
            generate_images=True
        )
        
        # Create presentation using the PresentationService with the AI-suggested theme
        presentation_id = await service.create_presentation_from_topic(
            user_id=user_id,
            title=title,
            topic=instructions,
            num_slides=7,
            generate_images=True,
            theme=suggested_theme  # Use the AI-suggested theme
        )
        
        if presentation_id:
            view_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
            logger.info(f"Created presentation with theme {suggested_theme}. View at: {view_url}")
            
            # Format the email body with the actual presentation link
            formatted_body = email_content.body.replace("[LINK]", view_url)
            if "[LINK]" not in formatted_body:
                # If [LINK] placeholder not found, append it to the body
                formatted_body += f"\n\nYou can access the presentation here: {view_url}"

            # Send email with presentation link using AI-generated content
            await send_email(
                user_id=user_id,
                instructions=instructions,
                subject=email_content.subject,
                body=formatted_body
            )
            
            return view_url
        else:
            raise Exception("Failed to create presentation")

    except Exception as e:
        logger.error(f"Error creating presentation: {str(e)}")
        raise

# Helper Functions
def _create_message(sender: str, to: str, subject: str, message_text: str) -> str:
    """Create a base64url encoded email message."""
    from email.mime.text import MIMEText
    import base64
    
    # Create the message
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    
    # Encode the message
    encoded_message = base64.urlsafe_b64encode(message.as_string().encode('utf-8')).decode('utf-8')
    return encoded_message

async def main():
    """Main entry point for creating presentations"""
    try:
        user_id = "107085158246892440905"  # Replace with actual user ID
        instructions = "Healthy living in green spaces"
        
        presentation_url = await create_presentation(
            user_id=user_id,
            instructions=instructions
        )
        print(f"Presentation created successfully! View at: {presentation_url}")
        
    except Exception as e:
        print(f"Error creating presentation: {str(e)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())