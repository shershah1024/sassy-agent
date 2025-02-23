import logging
from typing import Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64

logger = logging.getLogger(__name__)

def _create_message(sender: str, to: str, subject: str, body: str) -> str:
    """Create a base64url encoded email message"""
    message = f"From: {sender}\nTo: {to}\nSubject: {subject}\n\n{body}"
    return base64.urlsafe_b64encode(message.encode()).decode()

async def send_email_with_credentials(
    credentials: Credentials,
    recipient_email: str,
    subject: str,
    body: str
) -> Dict[str, Any]:
    """Send an email using Gmail API with provided credentials"""
    try:
        # Build Gmail service
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