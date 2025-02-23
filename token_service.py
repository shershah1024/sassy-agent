from supabase import create_client
import os
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import logging
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class TokenService:
    def __init__(self):
        # Check and log all required environment variables
        required_vars = {
            'SUPABASE_URL': os.getenv('SUPABASE_URL'),
            'SUPABASE_ANON_KEY': os.getenv('SUPABASE_ANON_KEY'),
            'GOOGLE_CLIENT_ID': os.getenv('GOOGLE_CLIENT_ID'),
            'GOOGLE_CLIENT_SECRET': os.getenv('GOOGLE_CLIENT_SECRET')
        }
        
        logger.info("Checking environment variables...")
        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        logger.info("All required environment variables found")
        self.supabase = create_client(required_vars['SUPABASE_URL'], required_vars['SUPABASE_ANON_KEY'])

    async def get_valid_token(self, user_id: str) -> Optional[str]:
        """
        Get a valid access token for the given user_id.
        Will automatically attempt to refresh if token is expired.
        Returns None if no valid token is found or refresh fails.
        """
        try:
            logger.info(f"Fetching token for user_id: {user_id}")
            # Get the user's auth record
            response = self.supabase.table('user_auth') \
                .select('*') \
                .eq('user_id', user_id) \
                .single() \
                .execute()

            logger.info(f"Full Supabase response: {response}")
            logger.info(f"Response data: {response.data if response else 'No data'}")

            if not response.data:
                logger.warning(f"No auth record found for user {user_id}")
                return None

            auth_record = response.data
            current_time = int(datetime.now().timestamp())
            
            # Log token details
            logger.info(f"Token details for user {user_id}:")
            logger.info(f"- Expires at: {auth_record['expires_at']} (timestamp)")
            logger.info(f"- Current time: {current_time} (timestamp)")
            logger.info(f"- Time until expiry: {auth_record['expires_at'] - current_time} seconds")
            logger.info(f"- Provider: {auth_record.get('provider', 'not specified')}")
            logger.info(f"- Has refresh token: {'refresh_token' in auth_record}")

            # Check if token is expired
            if current_time >= auth_record['expires_at']:
                logger.info(f"Token is expired for user {user_id}, attempting to refresh...")
                refreshed_token = await self.refresh_token(auth_record)
                if refreshed_token:
                    logger.info(f"Successfully refreshed token for user {user_id}")
                    return refreshed_token
                logger.warning(f"Failed to refresh token for user {user_id}")
                return None

            logger.info(f"Valid token found for user {user_id}")
            return auth_record['access_token']

        except Exception as e:
            logger.error(f"Error fetching token for user {user_id}: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {getattr(e, 'details', 'No details available')}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def refresh_token(self, auth_record: Dict[str, Any]) -> Optional[str]:
        """
        Refresh an expired token using the refresh token.
        Returns the new access token if successful, None otherwise.
        """
        try:
            logger.info(f"Attempting to refresh token for user {auth_record['user_id']}")
            
            # Create credentials object
            credentials = Credentials(
                token=auth_record['access_token'],
                refresh_token=auth_record['refresh_token'],
                token_uri='https://oauth2.googleapis.com/token',
                client_id=os.getenv('GOOGLE_CLIENT_ID'),
                client_secret=os.getenv('GOOGLE_CLIENT_SECRET')
            )

            # Refresh the token
            logger.info("Refreshing token...")
            request = Request()
            credentials.refresh(request)
            
            # Get new expiry timestamp
            new_expires_at = int(credentials.expiry.timestamp())
            logger.info(f"New token expires at: {new_expires_at}")
            
            # Update the token in Supabase
            success = await self.save_token(
                user_id=auth_record['user_id'],
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                expires_at=new_expires_at,
                provider='google'
            )
            
            if success:
                logger.info("Successfully saved refreshed token")
                return credentials.token
            else:
                logger.error("Failed to save refreshed token")
                return None

        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {getattr(e, 'details', 'No details available')}")
            return None

    async def save_token(self, 
                        user_id: str, 
                        access_token: str, 
                        refresh_token: str,
                        expires_at: int,
                        provider: str = 'google') -> bool:
        """
        Save or update token information for a user
        """
        try:
            logger.info(f"Attempting to save token for user {user_id}")
            current_time = datetime.now().isoformat()
            
            # Check if record exists
            logger.info("Checking if record exists...")
            response = self.supabase.table('user_auth') \
                .select('id') \
                .eq('user_id', user_id) \
                .single() \
                .execute()

            logger.info(f"Record check response: {response}")

            data = {
                'user_id': user_id,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_at': expires_at,
                'provider': provider,
                'updated_at': current_time
            }

            if response.data:
                logger.info(f"Updating existing record for user {user_id}")
                update_response = self.supabase.table('user_auth') \
                    .update(data) \
                    .eq('user_id', user_id) \
                    .execute()
                logger.info(f"Update response: {update_response}")
            else:
                logger.info(f"Creating new record for user {user_id}")
                data['created_at'] = current_time
                insert_response = self.supabase.table('user_auth') \
                    .insert(data) \
                    .execute()
                logger.info(f"Insert response: {insert_response}")

            return True

        except Exception as e:
            logger.error(f"Error saving token for user {user_id}: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {getattr(e, 'details', 'No details available')}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    async def delete_token(self, user_id: str) -> bool:
        """
        Delete token information for a user
        """
        try:
            self.supabase.table('user_auth') \
                .delete() \
                .eq('user_id', user_id) \
                .execute()
            return True
        except Exception as e:
            print(f"Error deleting token: {str(e)}")
            return False 