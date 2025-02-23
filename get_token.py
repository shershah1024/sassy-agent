import pickle

def get_token_from_pickle():
    """Extract the access token from token.pickle"""
    try:
        with open('token.pickle', 'rb') as token_file:
            creds = pickle.load(token_file)
            if creds and creds.valid:
                return creds.token
            else:
                print("Token is not valid. Please run setup_google_auth.py first.")
                return None
    except FileNotFoundError:
        print("token.pickle not found. Please run setup_google_auth.py first.")
        return None

if __name__ == "__main__":
    token = get_token_from_pickle()
    if token:
        print("\nYour Bearer token:")
        print(token)
        print("\nUse this token in the Authorization header like this:")
        print(f"Authorization: Bearer {token}") 