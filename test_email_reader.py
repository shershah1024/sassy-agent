import asyncio
from google_api_wrapper import read_emails
from presentation_service import PresentationService
import json

async def test_read_emails():
    try:
        # Default user ID from the code
        user_id = '107085158246892440905'
        print("\nFetching recent emails...")
        
        # First get credentials
        service = PresentationService()
        credentials = await service.get_presentation_credentials(user_id)
        
        if not credentials:
            print("Failed to get credentials")
            return
            
        # Now read_emails is async, so we use await
        emails = await read_emails(user_id, 'show recent emails')
        
        print('\nReceived Emails:')
        print('=' * 50)
        
        if not emails:
            print("No emails found.")
            return
            
        for idx, email in enumerate(emails, 1):
            print(f'\nEmail #{idx}')
            print('-' * 30)
            print(f"Subject: {email.get('subject', 'N/A')}")
            print(f"From: {email.get('from', 'N/A')}")
            print(f"Preview: {email.get('snippet', 'N/A')}")
            
        # Print raw data for debugging
        print('\nRaw Email Data:')
        print('=' * 50)
        print(json.dumps(emails, indent=2))
        
    except Exception as e:
        print(f'Error: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_read_emails()) 