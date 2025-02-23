import pytest
from datetime import datetime
from document_services import DocumentService
from report_models import (
    Report, Section, TextContent, ImageGenerationPrompt,
    TableContent, ChartContent, CodeBlockContent, QuoteContent,
    ReportMetadata, InferredDetails
)
import asyncio
from get_token import get_token_from_pickle

@pytest.fixture
async def document_service():
    """Fixture to create a DocumentService instance"""
    token = get_token_from_pickle()
    if not token:
        pytest.skip("No valid token found. Please run setup_google_auth.py first.")
    return DocumentService(access_token=token)

def create_sample_report():
    """Create a sample report for testing"""
    return Report(
        title="Test Structured Report",
        style="TECHNICAL",
        metadata=ReportMetadata(
            author="Test Author",
            date=datetime.now().isoformat(),
            version="1.0",
            keywords=["test", "automation", "documentation"],
            abstract="This is a test report generated for automated testing purposes."
        ),
        sections=[
            Section(
                type="EXECUTIVE_SUMMARY",
                title="Executive Summary",
                content=[
                    TextContent(
                        content="This is an executive summary of the test report.",
                        style="EMPHASIS"
                    )
                ]
            ),
            Section(
                type="INTRODUCTION",
                title="Introduction",
                content=[
                    TextContent(
                        content="This is the introduction section of our test report.",
                        style="NORMAL"
                    ),
                    QuoteContent(
                        text="Testing is the process of evaluating a system or its component(s) with the intent to find whether it satisfies the specified requirements or not.",
                        author="Anonymous",
                        year="2023"
                    )
                ]
            ),
            Section(
                type="METHODOLOGY",
                title="Test Methodology",
                content=[
                    TextContent(
                        content="Our testing methodology includes the following components:",
                        style="NORMAL"
                    ),
                    TableContent(
                        headers=["Step", "Description", "Expected Outcome"],
                        rows=[
                            ["1", "Initialize system", "System ready"],
                            ["2", "Run tests", "Tests complete"],
                            ["3", "Analyze results", "Results documented"]
                        ]
                    ),
                    CodeBlockContent(
                        code="def test_function():\n    assert True",
                        language="python",
                        caption="Sample Test Code"
                    )
                ]
            )
        ],
        style_reasoning="Technical style chosen due to the nature of the test report",
        content_flow=[
            "Executive summary provides overview",
            "Introduction sets context",
            "Methodology details the testing process"
        ],
        inferred_details=InferredDetails(
            audience="Technical team members",
            purpose="Demonstrate structured report generation",
            key_findings=[
                "Structured reports can be generated",
                "Multiple content types are supported",
                "Format is flexible and extensible"
            ],
            suggested_next_steps=[
                "Implement additional content types",
                "Add more formatting options",
                "Enhance error handling"
            ]
        )
    )

@pytest.mark.asyncio
async def test_structured_report_creation():
    """Test creating a structured report"""
    service = DocumentService()
    report = create_sample_report()
    
    try:
        print("\nCreating structured report...")
        doc_info = await service.create_structured_report(report)
        assert doc_info["document_id"], "Document ID should be present"
        assert doc_info["url"], "Document URL should be present"
        print(f"Document created successfully. ID: {doc_info['document_id']}")
        print(f"Document URL: {doc_info['url']}")
        
        # Store document ID for further operations
        document_id = doc_info["document_id"]
        
        # Export as PDF
        print("\nExporting as PDF...")
        pdf_content = await service.export_document(document_id, "pdf")
        assert pdf_content, "PDF content should not be empty"
        
        # Save PDF for verification
        with open("test_structured_report.pdf", "wb") as f:
            f.write(pdf_content)
        print("PDF saved as 'test_structured_report.pdf'")
        
        # Export as DOCX
        print("\nExporting as DOCX...")
        docx_content = await service.export_document(document_id, "docx")
        assert docx_content, "DOCX content should not be empty"
        
        # Save DOCX for verification
        with open("test_structured_report.docx", "wb") as f:
            f.write(docx_content)
        print("DOCX saved as 'test_structured_report.docx'")
        
        # Clean up
        print("\nDeleting test document...")
        await service.delete_document(document_id)
        print("Document deleted successfully")
        
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")

if __name__ == "__main__":
    # Run the test directly if this file is executed
    asyncio.run(test_structured_report_creation()) 