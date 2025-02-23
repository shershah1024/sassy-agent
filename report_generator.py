from typing import Optional, List, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import logging
from datetime import datetime
from report_models import Report, Section, ImageGenerationPrompt, ReportMetadata, ReportGenerationInput
import json
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self, credentials: Credentials):
        """Initialize the report generator with Google credentials and Azure OpenAI client"""
        self.docs_service = build('docs', 'v1', credentials=credentials)
        self.drive_service = build('drive', 'v3', credentials=credentials)
        
        # Initialize Azure OpenAI client
        self.openai_client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    async def generate_complete_report(self, input_data: ReportGenerationInput) -> Report:
        """Generate a complete report from topic and content"""
        try:
            # Generate the complete report structure
            completion = self.openai_client.chat.completions.create(
                model=self.deployment_name,
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
                        "content": f"Generate a complete report structure for topic: '{input_data.topic}'. Context: {input_data.content}"
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

            # Parse the response
            report_data = json.loads(completion.choices[0].message.function_call.arguments)
            
            # Process sections
            sections = []
            for section_data in report_data["sections"]:
                # Create image prompts if present
                image_prompts = None
                if "image_prompts" in section_data:
                    image_prompts = [ImageGenerationPrompt(**prompt) for prompt in section_data["image_prompts"]]

                # Create subsections if present
                subsections = None
                if "subsections" in section_data:
                    subsections = [Section(
                        title=sub["title"],
                        content=sub["content"],
                        image_prompts=None,
                        subsections=None
                    ) for sub in section_data["subsections"]]

                sections.append(Section(
                    title=section_data["title"],
                    content=section_data["content"],
                    image_prompts=image_prompts,
                    subsections=subsections
                ))

            # Create the complete report
            return Report(
                metadata=ReportMetadata(
                    title=input_data.title,
                    author=input_data.author,
                    date=datetime.now(),
                    version=input_data.version,
                    tags=input_data.tags
                ),
                executive_summary=report_data["executive_summary"],
                sections=sections,
                references=report_data.get("references"),
                appendices=None
            )

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise

    def create_report(self, report: Report) -> Dict[str, str]:
        """Create a new Google Doc with the structured report content"""
        try:
            # Create a new Google Doc
            doc = self.docs_service.documents().create(
                body={'title': report.metadata.title}
            ).execute()
            document_id = doc['documentId']

            # Generate the complete report content
            requests = self._generate_report_requests(report)

            # Apply the updates to the document
            self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()

            # Generate the document URL
            doc_url = f"https://docs.google.com/document/d/{document_id}/edit"

            return {
                "document_id": document_id,
                "title": report.metadata.title,
                "url": doc_url
            }

        except Exception as e:
            logger.error(f"Error creating report: {str(e)}")
            raise

    def _generate_report_requests(self, report: Report) -> List[Dict[str, Any]]:
        """Generate a list of requests for document updates"""
        requests = []
        current_index = 1  # Start after title

        # Add metadata
        requests.extend(self._format_metadata(report.metadata, current_index))
        current_index += self._calculate_metadata_length(report.metadata)

        # Add executive summary if present
        if report.executive_summary:
            requests.extend(self._format_executive_summary(report.executive_summary, current_index))
            current_index += len(report.executive_summary) + 2  # +2 for header and newline

        # Add sections
        for section in report.sections:
            section_requests, length = self._format_section(section, current_index)
            requests.extend(section_requests)
            current_index += length

        # Add references if present
        if report.references:
            requests.extend(self._format_references(report.references, current_index))
            current_index += len(report.references) + 2

        # Add appendices if present
        if report.appendices:
            requests.extend(self._format_appendices(report.appendices, current_index))

        return requests

    def _format_metadata(self, metadata: 'ReportMetadata', start_index: int) -> List[Dict[str, Any]]:
        """Format metadata section requests"""
        requests = []
        
        # Add title
        requests.append({
            'insertText': {
                'location': {'index': start_index},
                'text': f"{metadata.title}\n"
            }
        })
        requests.append({
            'updateParagraphStyle': {
                'range': {
                    'startIndex': start_index,
                    'endIndex': start_index + len(metadata.title) + 1
                },
                'paragraphStyle': {
                    'namedStyleType': 'TITLE',
                    'alignment': 'CENTER'
                },
                'fields': 'namedStyleType,alignment'
            }
        })

        # Add metadata block
        metadata_text = (
            f"\nAuthor: {metadata.author}\n"
            f"Date: {metadata.date.strftime('%Y-%m-%d')}\n"
        )
        if metadata.version:
            metadata_text += f"Version: {metadata.version}\n"
        if metadata.tags:
            metadata_text += f"Tags: {', '.join(metadata.tags)}\n"
        
        requests.append({
            'insertText': {
                'location': {'index': start_index + len(metadata.title) + 1},
                'text': metadata_text
            }
        })

        return requests

    def _format_executive_summary(self, summary: str, start_index: int) -> List[Dict[str, Any]]:
        """Format executive summary section requests"""
        requests = []
        
        # Add header
        requests.append({
            'insertText': {
                'location': {'index': start_index},
                'text': "Executive Summary\n"
            }
        })
        requests.append({
            'updateParagraphStyle': {
                'range': {
                    'startIndex': start_index,
                    'endIndex': start_index + len("Executive Summary") + 1
                },
                'paragraphStyle': {
                    'namedStyleType': 'HEADING_1'
                },
                'fields': 'namedStyleType'
            }
        })

        # Add summary content
        requests.append({
            'insertText': {
                'location': {'index': start_index + len("Executive Summary") + 1},
                'text': f"{summary}\n\n"
            }
        })

        return requests

    def _format_section(self, section: Section, start_index: int, level: int = 1) -> tuple[List[Dict[str, Any]], int]:
        """Format section requests and return the requests and total length"""
        requests = []
        current_index = start_index
        total_length = 0

        # Add section title
        requests.append({
            'insertText': {
                'location': {'index': current_index},
                'text': f"{section.title}\n"
            }
        })
        requests.append({
            'updateParagraphStyle': {
                'range': {
                    'startIndex': current_index,
                    'endIndex': current_index + len(section.title) + 1
                },
                'paragraphStyle': {
                    'namedStyleType': f'HEADING_{level}'
                },
                'fields': 'namedStyleType'
            }
        })
        total_length += len(section.title) + 1

        # Add section content
        requests.append({
            'insertText': {
                'location': {'index': current_index + total_length},
                'text': f"{section.content}\n\n"
            }
        })
        total_length += len(section.content) + 2

        # Process image prompts if present
        if section.image_prompts:
            for prompt in section.image_prompts:
                # Here we would generate the image and add it to the document
                # This is a placeholder for the image generation logic
                image_placeholder = f"[Image: {prompt.description}]\n"
                requests.append({
                    'insertText': {
                        'location': {'index': current_index + total_length},
                        'text': image_placeholder
                    }
                })
                total_length += len(image_placeholder)

        # Process subsections recursively
        if section.subsections:
            for subsection in section.subsections:
                subsection_requests, subsection_length = self._format_section(
                    subsection,
                    current_index + total_length,
                    level + 1
                )
                requests.extend(subsection_requests)
                total_length += subsection_length

        return requests, total_length

    def _format_references(self, references: List[str], start_index: int) -> List[Dict[str, Any]]:
        """Format references section requests"""
        requests = []
        
        # Add header
        requests.append({
            'insertText': {
                'location': {'index': start_index},
                'text': "References\n"
            }
        })
        requests.append({
            'updateParagraphStyle': {
                'range': {
                    'startIndex': start_index,
                    'endIndex': start_index + len("References") + 1
                },
                'paragraphStyle': {
                    'namedStyleType': 'HEADING_1'
                },
                'fields': 'namedStyleType'
            }
        })

        # Add references
        reference_text = "\n".join(f"• {ref}" for ref in references) + "\n\n"
        requests.append({
            'insertText': {
                'location': {'index': start_index + len("References") + 1},
                'text': reference_text
            }
        })

        return requests

    def _format_appendices(self, appendices: Dict[str, Any], start_index: int) -> List[Dict[str, Any]]:
        """Format appendices section requests"""
        requests = []
        
        # Add header
        requests.append({
            'insertText': {
                'location': {'index': start_index},
                'text': "Appendices\n"
            }
        })
        requests.append({
            'updateParagraphStyle': {
                'range': {
                    'startIndex': start_index,
                    'endIndex': start_index + len("Appendices") + 1
                },
                'paragraphStyle': {
                    'namedStyleType': 'HEADING_1'
                },
                'fields': 'namedStyleType'
            }
        })

        # Add appendices content
        appendix_text = json.dumps(appendices, indent=2) + "\n"
        requests.append({
            'insertText': {
                'location': {'index': start_index + len("Appendices") + 1},
                'text': appendix_text
            }
        })

        return requests

    def _calculate_metadata_length(self, metadata: 'ReportMetadata') -> int:
        """Calculate the total length of the metadata section"""
        length = len(metadata.title) + 1  # Title + newline
        length += len(metadata.author) + 8  # "Author: " + content + newline
        length += 28  # "Date: YYYY-MM-DD" + newline
        if metadata.version:
            length += len(metadata.version) + 9  # "Version: " + content + newline
        if metadata.tags:
            length += len(", ".join(metadata.tags)) + 7  # "Tags: " + content + newline
        return length 