import asyncio
import json
from datetime import datetime
import httpx
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

async def test_report_generation():
    """Test the report generation and creation process"""
    
    # Define the test report generation request
    generation_request = {
        "title": "AI Technology Trends 2024",
        "author": "AI Research Team",
        "version": "1.0",
        "tags": ["AI", "technology", "trends", "2024"],
        "sections": [
            {
                "title": "Large Language Models",
                "context": "Current state and advancements in LLMs, focusing on GPT-4 and its competitors, including performance metrics and real-world applications"
            },
            {
                "title": "AI in Healthcare",
                "context": "Analysis of how AI is transforming healthcare, including diagnostic tools, drug discovery, and personalized medicine in 2024"
            },
            {
                "title": "Ethical AI Development",
                "context": "Discussion of ethical considerations in AI development, including bias mitigation, transparency, and responsible AI practices"
            }
        ]
    }

    # Your Google OAuth token (you'll need to provide this)
    auth_token = "YOUR_GOOGLE_AUTH_TOKEN"
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Generate the report content
            print("Generating report content...")
            response = await client.post(
                "http://localhost:8000/reports/generate",
                json=generation_request,
                headers=headers
            )
            
            if response.status_code != 200:
                print(f"Error generating report: {response.text}")
                return
            
            report_content = response.json()
            print("\nGenerated Report Structure:")
            print(json.dumps(report_content, indent=2))
            
            # Step 2: Create the Google Doc
            print("\nCreating Google Doc...")
            doc_response = await client.post(
                "http://localhost:8000/reports",
                json=report_content,
                headers=headers
            )
            
            if doc_response.status_code != 200:
                print(f"Error creating Google Doc: {doc_response.text}")
                return
            
            doc_result = doc_response.json()
            print("\nGoogle Doc Created Successfully!")
            print(f"Title: {doc_result['title']}")
            print(f"Document ID: {doc_result['document_id']}")
            print(f"URL: {doc_result['url']}")
            
        except Exception as e:
            print(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_report_generation()) 