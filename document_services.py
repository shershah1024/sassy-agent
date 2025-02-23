from __future__ import print_function
import os.path
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from report_models import Report, Section, TextContent, ImageGenerationPrompt, TableContent, ChartContent, CodeBlockContent, QuoteContent
import pickle
from typing import Dict, List, Any
from storage_service import StorageService

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file'
]

class DocumentService:
    def __init__(self, access_token: str = None):
        self.creds = None
        self.docs_service = None
        self.drive_service = None
        self.storage_service = StorageService()
        if access_token:
            self._authenticate_with_token(access_token)
        else:
            self._authenticate_with_pickle()

    def _authenticate_with_token(self, access_token: str):
        """Authenticate using a Bearer token"""
        try:
            self.creds = Credentials(
                token=access_token,
                scopes=SCOPES
            )
            self.docs_service = build('docs', 'v1', credentials=self.creds)
            self.drive_service = build('drive', 'v3', credentials=self.creds)
        except Exception as e:
            raise Exception(f"Error authenticating with token: {str(e)}")

    def _authenticate_with_pickle(self):
        """Authenticate using the pickle file"""
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except RefreshError:
                    if os.path.exists('credentials.json'):
                        flow = InstalledAppFlow.from_client_secrets_file(
                            'credentials.json', SCOPES)
                        self.creds = flow.run_local_server(port=0)
            else:
                if os.path.exists('credentials.json'):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    self.creds = flow.run_local_server(port=0)
                else:
                    raise FileNotFoundError("credentials.json file not found")

            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

        self.docs_service = build('docs', 'v1', credentials=self.creds)
        self.drive_service = build('drive', 'v3', credentials=self.creds)

    def _create_text_style_request(self, text: str, style: str, start_index: int) -> list:
        """Create style requests for text content"""
        requests = []
        
        # Add text
        requests.append({
            'insertText': {
                'location': {'index': start_index},
                'text': f"{text}\n"
            }
        })
        
        # Apply style
        if style == 'EMPHASIS':
            requests.append({
                'updateTextStyle': {
                    'range': {
                        'startIndex': start_index,
                        'endIndex': start_index + len(text)
                    },
                    'textStyle': {'bold': True},
                    'fields': 'bold'
                }
            })
        elif style == 'HIGHLIGHT':
            requests.append({
                'updateTextStyle': {
                    'range': {
                        'startIndex': start_index,
                        'endIndex': start_index + len(text)
                    },
                    'textStyle': {'backgroundColor': {'color': {'rgbColor': {'red': 1, 'green': 1, 'blue': 0}}}},
                    'fields': 'backgroundColor'
                }
            })
        
        return requests

    def _create_table_request(self, table: TableContent, start_index: int) -> list:
        """Create requests for table content"""
        requests = []
        
        # Create table
        requests.append({
            'insertTable': {
                'location': {'index': start_index},
                'rows': len(table.rows) + 1,  # +1 for headers
                'columns': len(table.headers)
            }
        })
        
        # Add headers
        current_index = start_index + 1
        for header in table.headers:
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': header
                }
            })
            current_index += 2  # +2 for cell spacing
        
        # Add rows
        for row in table.rows:
            for cell in row:
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': cell
                    }
                })
                current_index += 2
        
        return requests

    async def create_report(self, title: str, content: Dict[str, List[Dict[str, Any]]]) -> dict:
        """
        Creates a new Google Doc with the specified content.
        Handles markdown-style formatting including headers, bold, italic, and bullet points.
        """
        try:
            # Create the document with title
            document = self.docs_service.documents().create(
                body={'title': title}
            ).execute()
            document_id = document.get('documentId')
            
            requests = []
            current_index = 1  # Start after title
            
            # Process each section
            for section in content["sections"]:
                # Add section heading
                heading = section["heading"]
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': f"{heading}\n"
                    }
                })
                
                # Style the heading
                requests.append({
                    'updateParagraphStyle': {
                        'range': {
                            'startIndex': current_index,
                            'endIndex': current_index + len(heading) + 1
                        },
                        'paragraphStyle': {
                            'namedStyleType': 'HEADING_1',
                            'spaceAbove': {'magnitude': 20, 'unit': 'PT'},
                            'spaceBelow': {'magnitude': 10, 'unit': 'PT'}
                        },
                        'fields': 'namedStyleType,spaceAbove,spaceBelow'
                    }
                })
                
                current_index += len(heading) + 1
                
                # Process each content item in the section
                for content_item in section["contents"]:
                    if content_item["type"] == "text":
                        text = content_item["content"]
                        style = content_item.get("style", "NORMAL")
                        
                        # Remove formatting markers before calculating length
                        clean_text = text.replace('§§', '').replace('§', '')
                        
                        # Insert the text
                        requests.append({
                            'insertText': {
                                'location': {'index': current_index},
                                'text': f"{clean_text}\n"
                            }
                        })
                        
                        # Apply paragraph style
                        style_request = {
                            'updateParagraphStyle': {
                                'range': {
                                    'startIndex': current_index,
                                    'endIndex': current_index + len(clean_text) + 1
                                },
                                'paragraphStyle': {
                                    'namedStyleType': style
                                },
                                'fields': 'namedStyleType'
                            }
                        }
                        
                        # Add bullet style and indentation if needed
                        if style == "BULLET":
                            indent_level = content_item.get("indent_level", 0)
                            style_request['updateParagraphStyle']['paragraphStyle'].update({
                                'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE',
                                'indentStart': {'magnitude': 36 + (indent_level * 18), 'unit': 'PT'},
                                'indentFirstLine': {'magnitude': 18, 'unit': 'PT'}
                            })
                            style_request['updateParagraphStyle']['fields'] = 'namedStyleType,bulletPreset,indentStart,indentFirstLine'
                        
                        # Add header specific styling
                        elif style in ["HEADING_1", "HEADING_2", "HEADING_3"]:
                            style_request['updateParagraphStyle']['paragraphStyle'].update({
                                'spaceAbove': {'magnitude': 20, 'unit': 'PT'},
                                'spaceBelow': {'magnitude': 10, 'unit': 'PT'}
                            })
                            style_request['updateParagraphStyle']['fields'] = 'namedStyleType,spaceAbove,spaceBelow'
                        
                        requests.append(style_request)
                        
                        # Handle inline formatting if present
                        if content_item.get("inline_formatting"):
                            # Track offset for clean text
                            offset = 0
                            
                            # Handle bold text (marked with §§)
                            text_to_process = text
                            while '§§' in text_to_process:
                                start = text_to_process.find('§§')
                                if start == -1:
                                    break
                                end = text_to_process.find('§§', start + 2)
                                if end == -1:
                                    break
                                
                                # Calculate clean text positions
                                clean_start = len(text_to_process[:start].replace('§§', '').replace('§', ''))
                                clean_end = len(text_to_process[:end].replace('§§', '').replace('§', ''))
                                
                                requests.append({
                                    'updateTextStyle': {
                                        'range': {
                                            'startIndex': current_index + clean_start,
                                            'endIndex': current_index + clean_end
                                        },
                                        'textStyle': {'bold': True},
                                        'fields': 'bold'
                                    }
                                })
                                
                                text_to_process = text_to_process[end + 2:]
                            
                            # Handle italic text (marked with §)
                            text_to_process = text
                            while '§' in text_to_process:
                                start = text_to_process.find('§')
                                if start == -1:
                                    break
                                end = text_to_process.find('§', start + 1)
                                if end == -1:
                                    break
                                
                                # Calculate clean text positions
                                clean_start = len(text_to_process[:start].replace('§§', '').replace('§', ''))
                                clean_end = len(text_to_process[:end].replace('§§', '').replace('§', ''))
                                
                                requests.append({
                                    'updateTextStyle': {
                                        'range': {
                                            'startIndex': current_index + clean_start,
                                            'endIndex': current_index + clean_end
                                        },
                                        'textStyle': {'italic': True},
                                        'fields': 'italic'
                                    }
                                })
                                
                                text_to_process = text_to_process[end + 1:]
                        
                        current_index += len(clean_text) + 1
                
                # Add extra newline after section
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': "\n"
                    }
                })
                current_index += 1
            
            # Execute the requests
            if requests:
                self.docs_service.documents().batchUpdate(
                    documentId=document_id,
                    body={'requests': requests}
                ).execute()

            return {
                'document_id': document_id,
                'url': f"https://docs.google.com/document/d/{document_id}/edit"
            }

        except Exception as e:
            raise Exception(f"Error creating report: {str(e)}")

    async def export_document(self, document_id: str, export_format: str, user_id: str = None) -> bytes:
        """Exports a Google Doc to the specified format and optionally uploads to storage."""
        try:
            mime_types = {
                'pdf': 'application/pdf',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            }

            if export_format not in mime_types:
                raise ValueError(f"Unsupported export format: {export_format}")

            mime_type = mime_types[export_format]
            
            request = self.drive_service.files().export_media(
                fileId=document_id,
                mimeType=mime_type
            )
            
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                _, done = downloader.next_chunk()

            file_content_bytes = file_content.getvalue()

            # If user_id is provided, upload to storage
            if user_id:
                file_name = f"document.{export_format}"
                storage_info = await self.storage_service.upload_document(
                    file_content_bytes,
                    file_name,
                    user_id
                )
                return storage_info

            return file_content_bytes

        except Exception as e:
            raise Exception(f"Error exporting document: {str(e)}")

    async def delete_document(self, document_id: str) -> None:
        """Deletes a Google Doc."""
        try:
            self.drive_service.files().delete(fileId=document_id).execute()
        except Exception as e:
            raise Exception(f"Error deleting document: {str(e)}") 