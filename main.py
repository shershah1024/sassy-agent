from fastapi import FastAPI, HTTPException, Header, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from document_generator import (
    DocumentGenerationRequest,
    GeneratedDocumentResponse,
    generate_and_create_document
)
from document_services import DocumentService
from token_service import TokenService
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Document Generation API",
    description="API for AI-powered document generation and management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "Accept", "user_id"],
    expose_headers=["Content-Type", "Authorization"],
)

# Create document router
document_router = APIRouter(prefix="/documents", tags=["documents"])

# Document endpoints
@document_router.post("/generate", response_model=GeneratedDocumentResponse)
async def generate_document(
    request: DocumentGenerationRequest,
    user_id: str = Header(..., description="User ID")
):
    """
    Generate a document using AI and optionally create it as a Google Doc.
    
    The endpoint will:
    1. Generate structured document content using AI
    2. Optionally create a Google Doc with the content
    3. Optionally export the document to PDF and/or DOCX
    4. Upload exported files to storage if requested
    """
    try:
        # Get valid token
        token_service = TokenService()
        token = await token_service.get_valid_token(user_id)
        if not token:
            raise HTTPException(
                status_code=401,
                detail="No valid token found for user"
            )
        
        # Create document service
        document_service = DocumentService(access_token=token)
        
        # Generate and create document
        response = await generate_and_create_document(request, document_service)
        return response
        
    except Exception as e:
        logger.error(f"Error in generate_document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Token endpoint
@app.post("/auth/save-token")
async def save_token(
    user_id: str,
    access_token: str,
    refresh_token: str,
    expires_at: int,
    provider: str = "google"
):
    """Save OAuth token information"""
    try:
        token_service = TokenService()
        success = await token_service.save_token(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            provider=provider
        )
        if success:
            return {"message": "Token saved successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add the document router to the app
app.include_router(document_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
