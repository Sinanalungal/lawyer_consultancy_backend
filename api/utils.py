from oauth2client import client
import urllib
import requests
from decouple import Config
import jwt
from django.conf import settings
# config = Config('.env')


def get_id_token_with_code_method_1(code):
    """
    Get ID token using OAuth2Client library.

    Args:
    - code (str): Authorization code.

    Returns:
    - str: ID token.
    """
    credentials = client.credentials_from_clientsecrets_and_code(
        'client_secret.json',
        ['email', 'profile'],
        code
    )
    return credentials.id_token


def get_id_token_with_code_method_2(code):
    """
    Get ID token using requests library.

    Args:
    - code (str): Authorization code.

    Returns:
    - dict: Decoded ID token payload.
    """
    token_endpoint = "https://oauth2.googleapis.com/token"
    payload = {
        'code': code,
        'client_id': settings.CLIENT_ID,
        'client_secret': settings.CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'redirect_uri': "postmessage",
    }
    body = urllib.parse.urlencode(payload)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(token_endpoint, data=body, headers=headers)

    if response.ok:
        id_token = response.json()['id_token']
        return jwt.decode(id_token, options={"verify_signature": False})
    else:
        return None
