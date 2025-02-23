from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from openai_utils import structured_openai_completion
import logging

logger = logging.getLogger(__name__)

class Section(BaseModel):
    title: str
    content: str

class DocumentContent(BaseModel):
    title: str
    sections: List[Section]
    summary: str
    keywords: List[str]
    metadata: Optional[Dict[str, str]] = None

class GeneratedDocumentResponse(BaseModel):
    content: DocumentContent
    document_info: Optional[Dict[str, Any]] = None
    storage_info: Optional[Dict[str, Dict[str, Any]]] = None

class DocumentGenerationRequest(BaseModel):
    topic: str
    context: Optional[str] = None
    user_id: str
    max_tokens: Optional[int] = 2000
    temperature: Optional[float] = 0.7
    auto_create: Optional[bool] = True
    export_formats: Optional[List[str]] = ["pdf", "docx"]

async def generate_document_content(
    topic: str,
    context: Optional[str] = None,
    max_tokens: int = 2000,
    temperature: float = 0.7,
) -> DocumentContent:
    """
    Generate structured document content using OpenAI completion.
    """
    instructions = """You are an expert document creator with deep knowledge across various fields. Your task is to create a comprehensive, well-structured document that demonstrates expertise, clarity, and engagement.

Create a document that includes:
1. A clear, attention-grabbing title that accurately reflects the content
2. Multiple sections that flow logically and cover the topic in depth
3. For each section:
   - Use markdown formatting for better readability
   - Use ### for subsection headers
   - Use **bold** for emphasis
   - Use bullet points (- or *) for lists
   - Structure content with clear hierarchy
4. A concise yet comprehensive summary
5. Relevant keywords for categorization and search
6. Optional metadata if relevant (e.g., target audience, difficulty level)

Guidelines for content:
- Make the content engaging and accessible while maintaining professional depth
- Use clear examples and real-world applications where relevant
- Include current trends, challenges, and future implications
- Balance technical accuracy with readability
- Structure sections to build upon each other logically
- Ensure each section has a clear purpose and adds value
- Include practical insights and actionable takeaways where appropriate
- Use proper markdown formatting throughout the document

The response should be factual, well-researched, and demonstrate expert understanding of the topic."""
    
    original_content = f"Topic to create document about: {topic}"
    if context:
        original_content += f"\nAdditional context and requirements: {context}"
        
    try:
        response = await structured_openai_completion(
            instructions=instructions,
            original_content=original_content,
            response_model=DocumentContent,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response
    except Exception as e:
        raise Exception(f"Failed to generate document: {str(e)}")

def convert_to_google_doc_content(document: DocumentContent) -> Dict[str, Any]:
    """
    Convert DocumentContent to the format expected by document_services.
    Properly handles markdown formatting including headers, bold, italic, and lists.
    """
    def process_markdown_content(content: str) -> List[Dict[str, Any]]:
        formatted_contents = []
        
        # Split content into paragraphs
        paragraphs = content.split('\n')
        current_list_items = []
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                # If we have accumulated list items, add them as a group
                if current_list_items:
                    formatted_contents.extend(current_list_items)
                    current_list_items = []
                continue
                
            # Process the paragraph text first to handle inline formatting
            processed_text = process_inline_formatting(paragraph.strip())
            
            # Handle headers (after processing inline formatting)
            if processed_text.startswith('### '):
                if current_list_items:
                    formatted_contents.extend(current_list_items)
                    current_list_items = []
                formatted_contents.append({
                    "type": "text",
                    "content": processed_text[4:],
                    "style": "HEADING_3"
                })
            elif processed_text.startswith('## '):
                if current_list_items:
                    formatted_contents.extend(current_list_items)
                    current_list_items = []
                formatted_contents.append({
                    "type": "text",
                    "content": processed_text[3:],
                    "style": "HEADING_2"
                })
            elif processed_text.startswith('# '):
                if current_list_items:
                    formatted_contents.extend(current_list_items)
                    current_list_items = []
                formatted_contents.append({
                    "type": "text",
                    "content": processed_text[2:],
                    "style": "HEADING_1"
                })
            # Handle bullet points
            elif paragraph.lstrip().startswith('- ') or paragraph.lstrip().startswith('* '):
                indent_level = len(paragraph) - len(paragraph.lstrip())
                content = paragraph.lstrip()[2:]  # Remove the bullet point
                content = process_inline_formatting(content)
                current_list_items.append({
                    "type": "text",
                    "content": content,
                    "style": "BULLET",
                    "indent_level": indent_level // 2,  # Convert spaces to logical indent levels
                    "inline_formatting": True
                })
            else:
                # If we have accumulated list items, add them before continuing
                if current_list_items:
                    formatted_contents.extend(current_list_items)
                    current_list_items = []
                
                formatted_contents.append({
                    "type": "text",
                    "content": processed_text,
                    "style": "NORMAL",
                    "inline_formatting": True
                })
        
        # Add any remaining list items
        if current_list_items:
            formatted_contents.extend(current_list_items)
        
        return formatted_contents

    def process_inline_formatting(text: str) -> str:
        """Process bold and italic markers in text."""
        # Handle bold text first (both ** and __)
        processed = ""
        i = 0
        while i < len(text):
            if i + 1 < len(text) and text[i:i+2] in ["**", "__"]:
                # Find the closing marker
                marker = text[i:i+2]
                end = text.find(marker, i + 2)
                if end != -1:
                    # Add the text before the marker
                    if i > 0:
                        processed += text[:i]
                    # Add the bold text with special markers
                    processed += "§§" + text[i+2:end] + "§§"
                    # Move to the rest of the text
                    text = text[end+2:]
                    i = 0
                    continue
            i += 1
        
        # Add any remaining text
        processed += text
        text = processed
        
        # Handle italic text (both * and _)
        processed = ""
        i = 0
        while i < len(text):
            if text[i] in ["*", "_"] and (i == 0 or text[i-1] != text[i]):
                # Find the closing marker
                marker = text[i]
                end = text.find(marker, i + 1)
                if end != -1 and end + 1 < len(text) and text[end+1] != marker:
                    # Add the text before the marker
                    if i > 0:
                        processed += text[:i]
                    # Add the italic text with special markers
                    processed += "§" + text[i+1:end] + "§"
                    # Move to the rest of the text
                    text = text[end+1:]
                    i = 0
                    continue
            i += 1
        
        # Add any remaining text
        processed += text
        
        return processed

    return {
        "sections": [
            {
                "heading": section.title,
                "contents": process_markdown_content(section.content)
            }
            for section in document.sections
        ]
    }

async def generate_and_create_document(
    request: DocumentGenerationRequest,
    document_service = None
) -> GeneratedDocumentResponse:
    """
    Generate document content and optionally create Google Doc with exports.
    """
    try:
        # Generate the document content
        content = await generate_document_content(
            topic=request.topic,
            context=request.context,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        
        response = GeneratedDocumentResponse(content=content)
        
        if request.auto_create and document_service:
            # Convert content to Google Doc format
            doc_content = convert_to_google_doc_content(content)
            
            # Create the document
            doc_info = await document_service.create_report(content.title, doc_content)
            response.document_info = doc_info
            
            # Export if requested
            if request.export_formats:
                storage_info = {}
                for format in request.export_formats:
                    result = await document_service.export_document(
                        document_id=doc_info["document_id"],
                        export_format=format,
                        user_id=request.user_id
                    )
                    storage_info[format] = result
                response.storage_info = storage_info
        
        return response
        
    except Exception as e:
        raise Exception(f"Failed to generate and create document: {str(e)}")

