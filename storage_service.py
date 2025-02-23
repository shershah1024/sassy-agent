from supabase import create_client
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

load_dotenv()

class StorageService:
    def __init__(self):
        logger.info("Initializing StorageService")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials")
            
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.bucket_name = "course_files"
        logger.info(f"Using bucket: {self.bucket_name}")
        
        # No need to ensure bucket exists since we're using an existing bucket
    
    async def upload_document(self, file_content: bytes, file_name: str, user_id: str) -> dict:
        """
        Upload a document to Supabase storage.
        
        Args:
            file_content: The binary content of the file
            file_name: Original file name
            user_id: ID of the user uploading the file
        
        Returns:
            dict: Information about the uploaded file including the public URL
        """
        try:
            logger.info(f"Starting document upload for user {user_id}, file: {file_name}")
            # Generate a unique file name
            extension = file_name.split('.')[-1]
            unique_id = str(uuid.uuid4())
            unique_name = f"{user_id}/{unique_id}.{extension}"
            logger.info(f"Generated unique name: {unique_name}")
            
            # Upload the file
            logger.info(f"Uploading file to bucket '{self.bucket_name}'")
            self.supabase.storage.from_(self.bucket_name).upload(
                unique_name,
                file_content,
                {"content-type": "application/octet-stream"}
            )
            logger.info("Upload completed")
            
            # Construct the public URL
            # Format: https://<project_id>.supabase.co/storage/v1/object/public/<bucket_name>/<file_path>
            project_id = self.supabase_url.split('//')[1].split('.')[0]
            public_url = f"https://{project_id}.supabase.co/storage/v1/object/public/{self.bucket_name}/{unique_name}"
            logger.info(f"Generated public URL: {public_url}")
            
            # Construct response
            response = {
                "file_name": file_name,
                "storage_path": unique_name,
                "public_url": public_url,
                "uploaded_at": datetime.now().isoformat(),
                "user_id": user_id,
                "bucket": self.bucket_name,
                "file_id": unique_id
            }
            logger.info(f"Upload successful, returning: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            raise Exception(f"Error uploading document: {str(e)}")
    
    async def delete_document(self, storage_path: str) -> bool:
        """
        Delete a document from storage.
        
        Args:
            storage_path: The path of the file in storage
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            logger.info(f"Deleting document: {storage_path}")
            self.supabase.storage.from_(self.bucket_name).remove([storage_path])
            logger.info(f"Successfully deleted document: {storage_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise Exception(f"Error deleting document: {str(e)}") 