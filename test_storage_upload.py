import asyncio
import aiohttp
from storage_service import StorageService

async def test_upload_from_endpoint():
    try:
        # Initialize storage service
        storage_service = StorageService()
        
        # Get PDF content from the endpoint
        async with aiohttp.ClientSession() as session:
            async with session.get(
                'http://localhost:8000/documents/1jLX6kkgbEFtj3Y_NbZDQuXJO6XIfEMWesdA8SlxBTcQ/export/pdf',
                headers={'user_id': '103206410753859569109'}
            ) as response:
                file_content = await response.read()
        
        # Upload to storage
        test_user_id = "test_user_123"
        result = await storage_service.upload_document(
            file_content=file_content,
            file_name="test_document.pdf",
            user_id=test_user_id
        )
        
        print("\nUpload successful!")
        print(f"File name: {result['file_name']}")
        print(f"Storage path: {result['storage_path']}")
        print(f"Public URL: {result['public_url']}")
        print(f"Uploaded at: {result['uploaded_at']}")
        
        return result
        
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_upload_from_endpoint()) 