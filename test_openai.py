import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import AzureOpenAI
import os

# Load environment variables
load_dotenv()

async def test_openai_report_generation():
    """Test the OpenAI report generation without Google Docs integration"""
    
    try:
        # Initialize Azure OpenAI client
        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-15-preview"
        )
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

        # Test input
        test_input = {
            "topic": "The Impact of Artificial Intelligence on Healthcare",
            "content": """
            Analyze how AI is transforming healthcare delivery, diagnosis, and treatment. 
            Include current applications, challenges, and future potential. 
            Consider both technical and ethical aspects, as well as impact on healthcare professionals and patients.
            """
        }

        print("Generating report content...")
        print("\nInput:")
        print(json.dumps(test_input, indent=2))
        print("\nSending request to OpenAI...")

        # Make the API call
        completion = client.chat.completions.create(
            model=deployment_name,
            response_format={"type": "json_object"},
            max_tokens=5000,
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": """You are a professional report writer and analyst. Generate a comprehensive report structure with:
                    1. Relevant sections based on the topic
                    2. Detailed content for each section
                    3. Appropriate subsections where needed
                    4. Image suggestions to visualize key points
                    5. An executive summary
                    6. Relevant references
                    Make the report thorough and well-structured."""
                },
                {
                    "role": "user",
                    "content": f"Generate a complete report structure for topic: '{test_input['topic']}'. Context: {test_input['content']}"
                }
            ],
            functions=[{
                "name": "generate_report",
                "description": "Generate a complete report structure",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "executive_summary": {"type": "string"},
                        "sections": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "content": {"type": "string"},
                                    "image_prompts": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "description": {"type": "string"},
                                                "style": {"type": "string"}
                                            },
                                            "required": ["description"]
                                        }
                                    },
                                    "subsections": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "title": {"type": "string"},
                                                "content": {"type": "string"}
                                            },
                                            "required": ["title", "content"]
                                        }
                                    }
                                },
                                "required": ["title", "content"]
                            }
                        },
                        "references": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["executive_summary", "sections"]
                }
            }]
        )

        # Parse and format the response
        report_data = json.loads(completion.choices[0].message.function_call.arguments)
        
        print("\nGenerated Report Structure:")
        print("==========================")
        
        print("\nExecutive Summary:")
        print("-----------------")
        print(report_data["executive_summary"])
        
        print("\nSections:")
        print("---------")
        for i, section in enumerate(report_data["sections"], 1):
            print(f"\n{i}. {section['title']}")
            print("Content:", section["content"][:200] + "..." if len(section["content"]) > 200 else section["content"])
            
            if "image_prompts" in section and section["image_prompts"]:
                print("\nImage Prompts:")
                for prompt in section["image_prompts"]:
                    print(f"- {prompt['description']}")
            
            if "subsections" in section and section["subsections"]:
                print("\nSubsections:")
                for j, subsection in enumerate(section["subsections"], 1):
                    print(f"{i}.{j}. {subsection['title']}")
        
        if "references" in report_data and report_data["references"]:
            print("\nReferences:")
            print("-----------")
            for ref in report_data["references"]:
                print(f"- {ref}")

        # Save the complete response to a file
        with open("generated_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        print("\nComplete report saved to 'generated_report.json'")

    except Exception as e:
        print(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_openai_report_generation()) 