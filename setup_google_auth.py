from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os
import pickle

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file'
]

def setup_google_auth():
    """
    Set up Google OAuth2 authentication and save the credentials.
    This only needs to be run once to generate the token.pickle file.
    """
    creds = None
    
    # Check if we have valid credentials saved
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError(
                    "credentials.json not found. Please download it from Google Cloud Console "
                    "and place it in the project root directory."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    print("Authentication successful! Token saved in 'token.pickle'")
    return creds

if __name__ == "__main__":
    print("Setting up Google OAuth2 authentication...")
    print("Please make sure you have placed your credentials.json file in the current directory.")
    print("A browser window will open for authentication if needed.")
    setup_google_auth() 