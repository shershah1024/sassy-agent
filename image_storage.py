import os
import logging
import requests
import time
import random
import string
import tempfile
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
logger = logging.getLogger(__name__)

class ImageStorage:
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

    async def store_image_from_url(self, image_url: str) -> Optional[str]:
        """
        Download an image from a URL and store it in Supabase
        Returns the public URL of the stored image
        """
        temp_file = None
        try:
            # Fetch the image from the URL
            image_response = requests.get(image_url, stream=True)
            if not image_response.ok:
                logger.error("Failed to fetch image from URL")
                return None

            # Generate unique filename for Supabase
            timestamp = int(time.time())
            random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            filename = f"generated_image_{timestamp}_{random_string}.jpg"

            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            logger.info(f"Created temporary file: {temp_file.name}")

            # Write the image content to the temporary file
            for chunk in image_response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            temp_file.close()

            # Upload to Supabase Storage
            try:
                with open(temp_file.name, 'rb') as f:
                    result = self.supabase.storage \
                        .from_('presentation_images') \
                        .upload(
                            path=filename,
                            file=f,
                            file_options={"content-type": "image/jpeg"}
                        )

                    if isinstance(result, dict) and result.get('error'):
                        logger.error(f"Failed to upload to Supabase: {result['error']}")
                        return None

            except Exception as e:
                logger.error(f"Error during Supabase upload: {str(e)}")
                return None

            # Construct the public URL
            public_url = self._construct_public_url(filename)
            
            # Verify URL is accessible
            try:
                verify_response = requests.head(public_url)
                if not verify_response.ok:
                    logger.error(f"Generated URL not accessible: {public_url}")
                    return None

                logger.info('URL verified as accessible')
                logger.info(f"Successfully stored image: {public_url}")
                return public_url

            except Exception as e:
                logger.error(f"Error verifying URL: {str(e)}")
                return None

        except Exception as e:
            logger.error(f"Error storing image: {str(e)}")
            return None
            
        finally:
            # Clean up the temporary file
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                    logger.info(f"Cleaned up temporary file: {temp_file.name}")
                except Exception as e:
                    logger.error(f"Error cleaning up temporary file: {str(e)}") 