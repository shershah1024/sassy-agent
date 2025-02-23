import pytest
import os
from document_services import DocumentService
import asyncio

@pytest.fixture
async def document_service():
    """Fixture to create a DocumentService instance"""
    service = DocumentService()
    return service

@pytest.mark.asyncio
async def test_document_lifecycle():
    """Test the complete lifecycle of a document: create, export, and delete"""
    # Initialize the service
    service = DocumentService()
    
    # Test data
    title = "Test Document"
    content = {
        "sections": [
            {
                "heading": "Introduction",
                "content": "This is a test document created for automated testing."
            },
            {
                "heading": "Main Content",
                "content": "This section contains the main content of our test document."
            },
            {
                "heading": "Conclusion",
                "content": "This concludes our test document."
            }
        ]
    }
    
    try:
        # 1. Create document
        print("\nCreating document...")
        doc_info = await service.create_report(title, content)
        assert doc_info["document_id"], "Document ID should be present"
        assert doc_info["url"], "Document URL should be present"
        print(f"Document created successfully. ID: {doc_info['document_id']}")
        print(f"Document URL: {doc_info['url']}")
        
        # Store document ID for further operations
        document_id = doc_info["document_id"]
        
        # 2. Export as PDF
        print("\nExporting as PDF...")
        pdf_content = await service.export_document(document_id, "pdf")
        assert pdf_content, "PDF content should not be empty"
        print("PDF export successful")
        
        # Save PDF to file for verification
        with open("test_document.pdf", "wb") as f:
            f.write(pdf_content)
        print("PDF saved as 'test_document.pdf'")
        
        # 3. Export as DOCX
        print("\nExporting as DOCX...")
        docx_content = await service.export_document(document_id, "docx")
        assert docx_content, "DOCX content should not be empty"
        print("DOCX export successful")
        
        # Save DOCX to file for verification
        with open("test_document.docx", "wb") as f:
            f.write(docx_content)
        print("DOCX saved as 'test_document.docx'")
        
        # 4. Delete document
        print("\nDeleting document...")
        await service.delete_document(document_id)
        print("Document deleted successfully")
        
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")

@pytest.mark.asyncio
async def test_invalid_export_format():
    """Test exporting with an invalid format"""
    service = DocumentService()
    
    # Create a test document first
    doc_info = await service.create_report("Test Doc", {
        "sections": [{"heading": "Test", "content": "Test content"}]
    })
    
    with pytest.raises(ValueError):
        await service.export_document(doc_info["document_id"], "invalid_format")
    
    # Cleanup
    await service.delete_document(doc_info["document_id"])

if __name__ == "__main__":
    # Run the test directly if this file is executed
    asyncio.run(test_document_lifecycle()) 