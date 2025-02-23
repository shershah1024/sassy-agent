# Google Services API

A FastAPI-based REST API that integrates with various Google services including Calendar, Gmail, Drive, Sheets, and Docs.

## Features

- Calendar API integration (create/delete events)
- Gmail API integration (read/send emails)
- Google Sheets API integration (create spreadsheets, add tabs, update values)
- Google Drive API integration (list files, create folders)
- Google Docs API integration (create/update documents)

## Prerequisites

- Python 3.8+
- Google Cloud Platform account
- Google OAuth 2.0 credentials

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Google OAuth 2.0 credentials:
   - Go to the [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select an existing one
   - Enable the following APIs:
     - Google Calendar API
     - Gmail API
     - Google Sheets API
     - Google Drive API
     - Google Docs API
   - Create OAuth 2.0 credentials
   - Download the credentials and save them as `credentials.json` in the project root

5. Create `.env` file:
```bash
cp .env.example .env
```
Then edit the `.env` file with your credentials.

## Running the API

Start the FastAPI server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Interactive API documentation (Swagger UI): `http://localhost:8000/docs`
- Alternative API documentation (ReDoc): `http://localhost:8000/redoc`

## API Endpoints

### Calendar
- `POST /calendar/events` - Create a calendar event
- `DELETE /calendar/events/{event_id}` - Delete a calendar event

### Gmail
- `GET /gmail/messages` - Get recent emails
- `POST /gmail/send` - Send an email

### Sheets
- `POST /sheets` - Create a new spreadsheet
- `POST /sheets/tabs` - Add a new tab to a spreadsheet
- `PUT /sheets/values` - Update values in a spreadsheet

### Drive
- `GET /drive/files` - List files in Google Drive
- `POST /drive/folders` - Create a new folder

### Docs
- `POST /docs` - Create a new document
- `PUT /docs/{document_id}` - Update document content

## Authentication

The API uses OAuth 2.0 for authentication. On first run, it will open a browser window for you to authenticate with your Google account. The credentials will be saved locally in `token.pickle` for future use.

## Error Handling

All endpoints include proper error handling and will return appropriate HTTP status codes and error messages when something goes wrong.

## Security Notes

- Never commit your `credentials.json` or `token.pickle` files
- Keep your `.env` file secure and never commit it to version control
- Regularly rotate your credentials
- Use environment variables for sensitive information
