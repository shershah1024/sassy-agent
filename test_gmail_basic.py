import asyncio
from token_service import TokenService
from google_services import GoogleServices
import logging
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sanitize_filename(filename: str) -> str:
    """Convert potentially unsafe filename to a safe one"""
    # Replace directory separators with underscores
    safe_name = filename.replace('/', '_').replace('\\', '_')
    # Remove any other potentially problematic characters
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '._- ')
    return safe_name

async def test_basic_gmail_functions(user_id: str):
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
    
    try:
        # 1. Read recent emails with attachment info
        logger.info("\n1. Testing email reading with attachments...")
        emails = google_services.read_emails(max_results=50)  # Increased to 50 to find emails with attachments
        logger.info(f"Found {len(emails)} recent emails")
        
        # Track emails with attachments
        emails_with_attachments = []
        total_attachments = 0
        
        logger.info("\nScanning emails for attachments...")
        for email in emails:
            if email['attachments']:
                emails_with_attachments.append(email)
                total_attachments += len(email['attachments'])
                logger.info(f"\nFound email with {len(email['attachments'])} attachment(s):")
                logger.info(f"Subject: {email['subject']}")
                logger.info(f"From: {email['from']}")
                logger.info(f"Date: {email['date']}")
                logger.info("Attachments:")
                for attachment in email['attachments']:
                    size_kb = attachment['size'] / 1024
                    logger.info(f"- {attachment['filename']}")
                    logger.info(f"  Type: {attachment['mimeType']}")
                    logger.info(f"  Size: {size_kb:.2f} KB")
        
        logger.info(f"\nSummary: Found {len(emails_with_attachments)} emails with attachments")
        logger.info(f"Total attachments found: {total_attachments}")
            
        # 2. Download attachments from the first email that has them
        if emails_with_attachments:
            logger.info("\n2. Testing attachment download...")
            email = emails_with_attachments[0]
            logger.info(f"Selected email for download test:")
            logger.info(f"Subject: {email['subject']}")
            logger.info(f"From: {email['from']}")
            logger.info(f"Date: {email['date']}")
            
            # Create downloads directory if it doesn't exist
            downloads_dir = 'gmail_downloads'
            os.makedirs(downloads_dir, exist_ok=True)
            
            for attachment in email['attachments']:
                # Create a safe filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_filename = sanitize_filename(f"{timestamp}_{attachment['filename']}")
                output_path = os.path.join(downloads_dir, safe_filename)
                
                logger.info(f"\nDownloading: {attachment['filename']}")
                logger.info(f"Saving to: {output_path}")
                
                success = google_services.download_attachment(
                    message_id=email['id'],
                    attachment_id=attachment['id'],
                    output_path=output_path
                )
                
                if success:
                    logger.info(f"Successfully downloaded {attachment['filename']}")
                    logger.info(f"Saved to {output_path}")
                else:
                    logger.error(f"Failed to download {attachment['filename']}")
        else:
            logger.info("\nNo emails with attachments found in the last 50 messages")
            
        # 3. Send a test email
        logger.info("\n3. Testing email sending...")
        test_email = "abdul.shahir@gmail.com"
        logger.info(f"Sending test email to: {test_email}")
        
        response = google_services.send_email(
            to=test_email,
            subject="Test Email from Gmail API",
            message_text="""
Hello from Gmail API!

This is a test email sent using the Gmail API through our GoogleServices class.
Testing basic email functionality.

Best regards,
Your Gmail API Test Script
            """.strip()
        )
        logger.info(f"Email sent successfully! Message ID: {response['id']}")
        
        logger.info("\nAll Gmail tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during Gmail operations: {str(e)}")

if __name__ == "__main__":
    USER_ID = "106573671377678694423"
    asyncio.run(test_basic_gmail_functions(USER_ID)) 