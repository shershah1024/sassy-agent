import os
import logging
import requests
import time
import random
import string
import tempfile
from typing import Optional, Dict, Union
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
logger = logging.getLogger(__name__)

class RecraftStorage:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL environment variable is required")
            
        self.supabase = create_client(
            self.supabase_url,
            os.getenv('SUPABASE_ANON_KEY')
        )

    def _construct_public_url(self, filename: str) -> str:
        """Construct the public URL for a file in Supabase storage"""
        return f"{self.supabase_url}/storage/v1/object/public/presentation_images/{filename}"

    async def store_recraft_image(self, image_data: Union[Dict, str]) -> Optional[str]:
        """
        Store a Recraft-generated image in Supabase.
        Accepts either a URL string or Recraft's image data dictionary.
        Returns the public URL of the stored image.
        """
        temp_file = None
        try:
            # Extract URL from image data if it's a dictionary
            if isinstance(image_data, dict):
                if 'url' not in image_data:
                    logger.error("No URL found in Recraft image data")
                    return None
                image_url = image_data['url']
                content_type = image_data.get('content_type', 'image/webp')
                original_filename = image_data.get('file_name', 'image.webp')
            else:
                image_url = image_data
                content_type = 'image/webp'  # Default for Recraft
                original_filename = 'image.webp'

            # Fetch the image
            logger.info(f"Fetching Recraft image from: {image_url}")
            response = requests.get(image_url, stream=True)
            if not response.ok:
                logger.error(f"Failed to fetch image: {response.status_code}")
                return None

            # Generate unique filename
            timestamp = int(time.time())
            random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            extension = original_filename.split('.')[-1]
            filename = f"recraft_{timestamp}_{random_string}.{extension}"

            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{extension}')
            logger.info(f"Created temporary file: {temp_file.name}")

            # Save image to temporary file
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            temp_file.close()

            # Upload to Supabase
            try:
                with open(temp_file.name, 'rb') as f:
                    result = self.supabase.storage \
                        .from_('presentation_images') \
                        .upload(
                            path=filename,
                            file=f,
                            file_options={"content-type": content_type}
                        )

                    if isinstance(result, dict) and result.get('error'):
                        logger.error(f"Supabase upload failed: {result['error']}")
                        return None

            except Exception as e:
                logger.error(f"Error during Supabase upload: {str(e)}")
                return None

            # Get public URL
            public_url = self._construct_public_url(filename)
            
            # Verify URL
            try:
                verify_response = requests.head(public_url)
                if verify_response.ok:
                    logger.info(f"Successfully stored Recraft image: {public_url}")
                    return public_url
                else:
                    logger.error(f"Generated URL not accessible: {public_url}")
                    return None

            except Exception as e:
                logger.error(f"Error verifying URL: {str(e)}")
                return None

        except Exception as e:
            logger.error(f"Error storing Recraft image: {str(e)}")
            return None
            
        finally:
            # Cleanup
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                    logger.info(f"Cleaned up temporary file: {temp_file.name}")
                except Exception as e:
                    logger.error(f"Error cleaning up temporary file: {str(e)}") 