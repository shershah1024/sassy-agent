from typing import Optional, List, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import logging
import uuid
from enum import Enum


logger = logging.getLogger(__name__)

# Simplified to just use BLANK layout
class SlideLayout(Enum):
    BLANK = "BLANK"

class ShapeType(Enum):
    TEXT_BOX = "TEXT_BOX"
    RECTANGLE = "RECTANGLE"
    OVAL = "OVAL"
    TRIANGLE = "TRIANGLE"

class GoogleServices:
    def __init__(self, access_token: str):
        """Initialize with just an access token from frontend"""
        self.creds = Credentials(token=access_token)
        self.initialize_services()

    def initialize_services(self):
        """Initialize all Google API services"""
        if not self.creds:
            raise ValueError("No credentials available")
            
        self.calendar_service = build('calendar', 'v3', credentials=self.creds)
        self.gmail_service = build('gmail', 'v1', credentials=self.creds)
        self.sheets_service = build('sheets', 'v4', credentials=self.creds)
        self.drive_service = build('drive', 'v3', credentials=self.creds)
        self.docs_service = build('docs', 'v1', credentials=self.creds)
        self.slides_service = build('slides', 'v1', credentials=self.creds)

    def create_presentation(self, title: str) -> Dict[str, Any]:
        """Create a new Google Slides presentation"""
        try:
            presentation = {
                'title': title
            }
            return self.slides_service.presentations().create(body=presentation).execute()
        except Exception as e:
            logger.error(f"Error creating presentation: {str(e)}")
            raise

    def update_presentation(self, presentation_id: str, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update a presentation with a batch update request"""
        try:
            return self.slides_service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()
        except Exception as e:
            logger.error(f"Error updating presentation: {str(e)}")
            raise

    def add_blank_slide(self, presentation_id: str, insertion_index: int = 0, 
                       slide_object_id: Optional[str] = None) -> Optional[str]:
        """Adds a new blank slide."""
        try:
            request = {
                'createSlide': {
                    'insertionIndex': str(insertion_index),
                    'slideLayoutReference': {'predefinedLayout': SlideLayout.BLANK.value}
                }
            }
            if slide_object_id:
                request['createSlide']['objectId'] = slide_object_id
            response = self.update_presentation(presentation_id, [request])
            replies = response.get('replies', [])
            if replies:
                created_slide = replies[0].get('createSlide', {})
                return created_slide.get('objectId')
            return None
        except Exception as e:
            logger.error(f"Error adding slide: {str(e)}")
            raise

    def add_shape(self, presentation_id: str, slide_object_id: str, shape_type: ShapeType,
                  element_id: Optional[str] = None, left: int = 100, top: int = 100,
                  width: int = 200, height: int = 100, fill_color: Optional[Dict[str, float]] = None) -> str:
        """Creates a shape on the slide with optional fill color."""
        try:
            shape_id = element_id if element_id else f"{shape_type.value}_{uuid.uuid4().hex[:10]}"
            requests = [{
                'createShape': {
                    'objectId': shape_id,
                    'shapeType': shape_type.value,
                    'elementProperties': {
                        'pageObjectId': slide_object_id,
                        'size': {
                            'height': {'magnitude': height, 'unit': 'PT'},
                            'width': {'magnitude': width, 'unit': 'PT'}
                        },
                        'transform': {
                            'scaleX': 1,
                            'scaleY': 1,
                            'translateX': left,
                            'translateY': top,
                            'unit': 'PT'
                        }
                    }
                }
            }]
            
            if fill_color:
                requests.append({
                    'updateShapeProperties': {
                        'objectId': shape_id,
                        'shapeProperties': {
                            'shapeBackgroundFill': {
                                'solidFill': {
                                    'color': {'rgbColor': fill_color}
                                }
                            }
                        },
                        'fields': 'shapeBackgroundFill'
                    }
                })
            
            self.update_presentation(presentation_id, requests)
            return shape_id
        except Exception as e:
            logger.error(f"Error adding shape: {str(e)}")
            raise

    def add_text_box(self, presentation_id: str, slide_object_id: str, text: str, 
                    element_id: Optional[str] = None, left: int = 100, top: int = 100, 
                    width: int = 300, height: int = 100) -> str:
        """Creates a text box and inserts the provided text."""
        try:
            shape_id = element_id if element_id else f"TextBox_{uuid.uuid4().hex[:10]}"
            requests = [{
                'createShape': {
                    'objectId': shape_id,
                    'shapeType': ShapeType.TEXT_BOX.value,
                    'elementProperties': {
                        'pageObjectId': slide_object_id,
                        'size': {
                            'height': {'magnitude': height, 'unit': 'PT'},
                            'width': {'magnitude': width, 'unit': 'PT'}
                        },
                        'transform': {
                            'scaleX': 1,
                            'scaleY': 1,
                            'translateX': left,
                            'translateY': top,
                            'unit': 'PT'
                        }
                    }
                }
            }, {
                'insertText': {
                    'objectId': shape_id,
                    'insertionIndex': 0,
                    'text': text
                }
            }]
            self.update_presentation(presentation_id, requests)
            return shape_id
        except Exception as e:
            logger.error(f"Error adding text box: {str(e)}")
            raise

    def update_text_style(self, presentation_id: str, object_id: str, style_dict: Dict[str, Any]) -> None:
        """Updates text style within the given object."""
        try:
            request = {
                'updateTextStyle': {
                    'objectId': object_id,
                    'style': style_dict,
                    'textRange': {
                        'type': 'ALL'
                    },
                    'fields': ','.join(style_dict.keys())
                }
            }
            self.update_presentation(presentation_id, [request])
        except Exception as e:
            logger.error(f"Error updating text style: {str(e)}")
            raise

    def add_image(self, presentation_id: str, slide_object_id: str, image_url: str,
                 element_id: Optional[str] = None, left: int = 100, top: int = 200,
                 width: int = 300, height: int = 200) -> str:
        """Inserts an image onto a slide."""
        try:
            image_id = element_id if element_id else f"Image_{uuid.uuid4().hex[:10]}"
            requests = [{
                'createImage': {
                    'objectId': image_id,
                    'url': image_url,
                    'elementProperties': {
                        'pageObjectId': slide_object_id,
                        'size': {
                            'height': {'magnitude': height, 'unit': 'PT'},
                            'width': {'magnitude': width, 'unit': 'PT'}
                        },
                        'transform': {
                            'scaleX': 1,
                            'scaleY': 1,
                            'translateX': left,
                            'translateY': top,
                            'unit': 'PT'
                        }
                    }
                }
            }]
            self.update_presentation(presentation_id, requests)
            return image_id
        except Exception as e:
            logger.error(f"Error adding image: {str(e)}")
            raise

    def set_slide_background(self, presentation_id: str, slide_object_id: str,
                           image_url: Optional[str] = None,
                           background_color: Optional[Dict[str, float]] = None) -> None:
        """Sets the slide background either to an image or a solid color."""
        try:
            requests = []
            if image_url:
                requests.append({
                    'updatePageProperties': {
                        'objectId': slide_object_id,
                        'pageProperties': {
                            'pageBackgroundFill': {
                                'stretchedPictureFill': {'contentUrl': image_url}
                            }
                        },
                        'fields': 'pageBackgroundFill'
                    }
                })
            elif background_color:
                requests.append({
                    'updatePageProperties': {
                        'objectId': slide_object_id,
                        'pageProperties': {
                            'pageBackgroundFill': {
                                'solidFill': {
                                    'color': {'rgbColor': background_color}
                                }
                            }
                        },
                        'fields': 'pageBackgroundFill'
                    }
                })
            if requests:
                self.update_presentation(presentation_id, requests)
        except Exception as e:
            logger.error(f"Error setting slide background: {str(e)}")
            raise

    # Calendar Methods
    def create_calendar_event(self, summary: str, start_time: str, end_time: str, 
                            description: Optional[str] = None, attendees: Optional[List[str]] = None,
                            recurrence: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a calendar event
        
        Args:
            summary: Event title
            start_time: Start time in ISO format with 'Z' suffix
            end_time: End time in ISO format with 'Z' suffix
            description: Optional event description
            attendees: Optional list of attendee email addresses
            recurrence: Optional list of recurrence rules (e.g., ["RRULE:FREQ=WEEKLY;COUNT=4"])
        """
        event = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_time, 'timeZone': 'UTC'},
            'end': {'dateTime': end_time, 'timeZone': 'UTC'},
        }
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        if recurrence:
            event['recurrence'] = recurrence
        
        return self.calendar_service.events().insert(calendarId='primary', body=event).execute()

    def delete_calendar_event(self, event_id: str) -> None:
        """Delete a calendar event"""
        self.calendar_service.events().delete(calendarId='primary', eventId=event_id).execute()

    def get_calendar_event(self, event_id: str) -> Dict[str, Any]:
        """Get details of a specific calendar event"""
        return self.calendar_service.events().get(calendarId='primary', eventId=event_id).execute()

    def update_calendar_event(self, event_id: str, summary: Optional[str] = None, 
                            description: Optional[str] = None, start_time: Optional[str] = None,
                            end_time: Optional[str] = None, attendees: Optional[List[str]] = None) -> Dict[str, Any]:
        """Update an existing calendar event"""
        # First get the existing event
        event = self.get_calendar_event(event_id)
        
        # Update only the provided fields
        if summary:
            event['summary'] = summary
        if description:
            event['description'] = description
        if start_time:
            event['start']['dateTime'] = start_time
        if end_time:
            event['end']['dateTime'] = end_time
        if attendees is not None:  # Allow empty list to remove attendees
            event['attendees'] = [{'email': email} for email in attendees]
        
        return self.calendar_service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event
        ).execute()

    def list_calendar_events(self, max_results: int = 10, 
                           time_min: Optional[str] = None,
                           time_max: Optional[str] = None,
                           query: Optional[str] = None) -> List[Dict[str, Any]]:
        """List calendar events with optional filtering"""
        # Prepare parameters
        params = {
            'calendarId': 'primary',
            'maxResults': max_results,
            'orderBy': 'startTime',
            'singleEvents': True
        }
        
        if time_min:
            params['timeMin'] = time_min
        if time_max:
            params['timeMax'] = time_max
        if query:
            params['q'] = query
            
        events_result = self.calendar_service.events().list(**params).execute()
        return events_result.get('items', [])

    def quick_add_event(self, text: str) -> Dict[str, Any]:
        """Quickly add an event using natural language text
        Example: "Meeting with John tomorrow at 3pm"
        """
        return self.calendar_service.events().quickAdd(
            calendarId='primary',
            text=text
        ).execute()

    def create_calendar(self, summary: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new calendar"""
        calendar_body = {
            'summary': summary,
            'timeZone': 'UTC'
        }
        if description:
            calendar_body['description'] = description
            
        return self.calendar_service.calendars().insert(body=calendar_body).execute()

    def delete_calendar(self, calendar_id: str) -> None:
        """Delete a calendar"""
        self.calendar_service.calendars().delete(calendarId=calendar_id).execute()

    def list_calendars(self) -> List[Dict[str, Any]]:
        """List all calendars"""
        calendars_result = self.calendar_service.calendarList().list().execute()
        return calendars_result.get('items', [])

    # Gmail Methods
    def read_emails(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """Read recent emails with their details"""
        logger.info(f"Starting to fetch {max_results} emails")
        
        try:
            # Get message list
            messages_list = self.gmail_service.users().messages().list(
                userId='me', maxResults=max_results).execute()
            logger.info(f"Found {len(messages_list.get('messages', []))} messages")

            messages = []
            for msg_ref in messages_list.get('messages', []):
                try:
                    # Get message details
                    msg = self.gmail_service.users().messages().get(
                        userId='me', 
                        id=msg_ref['id'],
                        format='full'  # Changed to 'full' to get attachment info
                    ).execute()
                    logger.info(f"Processing message ID: {msg_ref['id']}")

                    # Get headers
                    headers = msg.get('payload', {}).get('headers', [])
                    email_data = {
                        'id': msg['id'],
                        'threadId': msg['threadId'],
                        'snippet': msg.get('snippet', 'No preview available'),
                        'subject': next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No subject'),
                        'from': next((h['value'] for h in headers if h['name'].lower() == 'from'), 'No sender'),
                        'date': next((h['value'] for h in headers if h['name'].lower() == 'date'), 'No date'),
                        'attachments': self._get_attachment_list(msg.get('payload', {}))
                    }
                    logger.info(f"Processed email: Subject: {email_data['subject'][:30]}...")
                    messages.append(email_data)

                except Exception as e:
                    logger.error(f"Error processing message {msg_ref['id']}: {str(e)}")
                    continue

            logger.info(f"Successfully processed {len(messages)} emails")
            return messages

        except Exception as e:
            logger.error(f"Failed to fetch emails: {str(e)}")
            raise

    def _get_attachment_list(self, payload: Dict) -> List[Dict[str, Any]]:
        """Extract attachment information from email payload"""
        attachments = []
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    attachments.append({
                        'id': part['body'].get('attachmentId'),
                        'filename': part['filename'],
                        'mimeType': part['mimeType'],
                        'size': part['body'].get('size', 0)
                    })
                # Check for nested parts
                if 'parts' in part:
                    attachments.extend(self._get_attachment_list(part))
        elif payload.get('filename'):
            attachments.append({
                'id': payload['body'].get('attachmentId'),
                'filename': payload['filename'],
                'mimeType': payload['mimeType'],
                'size': payload['body'].get('size', 0)
            })
            
        return attachments

    def download_attachment(self, message_id: str, attachment_id: str, output_path: str) -> bool:
        """Download an email attachment
        
        Args:
            message_id: ID of the email message
            attachment_id: ID of the attachment
            output_path: Path where to save the attachment
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            attachment = self.gmail_service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()

            if 'data' in attachment:
                import base64
                file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
                
                with open(output_path, 'wb') as f:
                    f.write(file_data)
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error downloading attachment: {str(e)}")
            return False

    def _get_email_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        if not payload:
            return ""

        # If the payload has a 'body' with data, it's a simple email
        if 'body' in payload and 'data' in payload['body']:
            import base64
            return base64.urlsafe_b64decode(payload['body']['data'].encode('ASCII')).decode('utf-8')

        # If the payload has parts, it's a multipart email
        if 'parts' in payload:
            parts = payload['parts']
            for part in parts:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        import base64
                        return base64.urlsafe_b64decode(part['body']['data'].encode('ASCII')).decode('utf-8')

        return ""

    def send_email(self, to: str, subject: str, message_text: str) -> Dict[str, Any]:
        """Send an email"""
        import base64
        from email.mime.text import MIMEText
        
        message = MIMEText(message_text)
        message['to'] = to
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        return self.gmail_service.users().messages().send(
            userId='me', body={'raw': raw_message}).execute()

    # Sheets Methods
    def create_spreadsheet(self, title: str) -> Dict[str, Any]:
        """Create a new Google Sheet"""
        spreadsheet = {
            'properties': {
                'title': title
            }
        }
        return self.sheets_service.spreadsheets().create(body=spreadsheet).execute()

    def add_sheet_tab(self, spreadsheet_id: str, title: str) -> Dict[str, Any]:
        """Add a new tab to an existing spreadsheet"""
        request = {
            'addSheet': {
                'properties': {
                    'title': title
                }
            }
        }
        return self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': [request]}
        ).execute()

    def update_values(self, spreadsheet_id: str, range_name: str, values: List[List[Any]]) -> Dict[str, Any]:
        """Update values in a spreadsheet"""
        body = {
            'values': values
        }
        return self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()

    # Drive Methods
    def list_files(self, page_size: int = 10) -> List[Dict[str, Any]]:
        """List files in Google Drive"""
        results = self.drive_service.files().list(
            pageSize=page_size,
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        return results.get('files', [])

    def create_folder(self, folder_name: str) -> Dict[str, Any]:
        """Create a new folder in Google Drive"""
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        return self.drive_service.files().create(body=file_metadata, fields='id').execute()

    # Docs Methods
    def create_document(self, title: str) -> Dict[str, Any]:
        """Create a new Google Doc"""
        body = {
            'title': title
        }
        return self.docs_service.documents().create(body=body).execute()

    def update_document(self, document_id: str, content: str) -> Dict[str, Any]:
        """Update content in a Google Doc"""
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': 1
                    },
                    'text': content
                }
            }
        ]
        return self.docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
