import asyncio
import aiohttp
import json
from typing import Dict, Any
import os
from datetime import datetime

async def create_document(session: aiohttp.ClientSession, user_id: str, content: Dict[str, Any]) -> Dict[str, Any]:
    """Create a Google Doc with the given content"""
    url = "http://localhost:8000/documents/create"
    headers = {
        "Content-Type": "application/json",
        "user_id": user_id
    }
    
    async with session.post(url, headers=headers, json=content) as response:
        if response.status != 200:
            error_text = await response.text()
            raise Exception(f"Failed to create document: {error_text}")
        return await response.json()

async def export_document(session: aiohttp.ClientSession, document_id: str, user_id: str, format: str) -> bytes:
    """Export the document to PDF or DOCX format"""
    url = f"http://localhost:8000/documents/{document_id}/export/{format}"
    headers = {
        "user_id": user_id
    }
    
    async with session.get(url, headers=headers) as response:
        if response.status != 200:
            error_text = await response.text()
            raise Exception(f"Failed to export document to {format}: {error_text}")
        return await response.read()

async def save_file(content: bytes, filename: str):
    """Save the file content to disk"""
    with open(filename, 'wb') as f:
        f.write(content)

async def run_pipeline():
    """Run the complete document pipeline"""
    # User ID and document content
    user_id = "103206410753859569109"
    content = {
        "title": "Comprehensive Analysis: The State of Artificial Intelligence in 2024",
        "content": {
            "sections": [
                {
                    "heading": "Executive Summary",
                    "contents": [
                        {
                            "type": "text",
                            "content": """This comprehensive report examines the evolution and impact of artificial intelligence across multiple sectors,
                            with a particular focus on recent developments in 2024. The analysis covers technical advancements,
                            practical applications, ethical considerations, and future projections. Our findings indicate significant
                            progress in several key areas, while also highlighting important challenges that need to be addressed.""",
                            "style": "NORMAL"
                        }
                    ]
                },
                {
                    "heading": "1. Introduction",
                    "contents": [
                        {
                            "type": "text",
                            "content": """Artificial Intelligence has become an integral part of modern society, transforming how we live, work,
                            and interact. This report provides a detailed analysis of current AI technologies, their applications,
                            and their implications for various sectors.""",
                            "style": "NORMAL"
                        }
                    ]
                },
                {
                    "heading": "2. Technical Analysis",
                    "contents": [
                        {
                            "type": "text",
                            "content": """2.1 Large Language Models
                            Recent developments in LLMs have shown remarkable progress in:
                            - Natural language understanding
                            - Code generation and analysis
                            - Multi-modal capabilities
                            - Few-shot learning""",
                            "style": "NORMAL"
                        },
                        {
                            "type": "text",
                            "content": """2.2 Computer Vision
                            Advancements in computer vision include:
                            - Real-time object detection
                            - 3D scene reconstruction
                            - Medical image analysis
                            - Autonomous navigation""",
                            "style": "NORMAL"
                        }
                    ]
                }
            ]
        },
        "user_id": user_id
    }

    try:
        async with aiohttp.ClientSession() as session:
            # Step 1: Create Google Doc and automatically export/upload PDF and DOCX
            print("\n1. Creating Google Doc and exporting files...")
            doc_info = await create_document(session, user_id, content)
            
            print("\n✓ Pipeline completed successfully!")
            print(f"Document created:")
            print(f"- Google Doc URL: {doc_info['url']}")
            print("\nExported files:")
            if 'storage_info' in doc_info:
                if 'pdf' in doc_info['storage_info']:
                    print(f"- PDF URL: {doc_info['storage_info']['pdf']['public_url']}")
                if 'docx' in doc_info['storage_info']:
                    print(f"- DOCX URL: {doc_info['storage_info']['docx']['public_url']}")

    except Exception as e:
        print(f"\n❌ Error in pipeline: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(run_pipeline()) 