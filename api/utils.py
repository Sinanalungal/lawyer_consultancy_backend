from oauth2client import client
import urllib
import requests
from decouple import config
import jwt
from decouple import Config
config = Config('.env')

def get_id_token_with_code_method_1(code):
    
    credentials = client.credentials_from_clientsecrets_and_code(
        'client_secret.json',
        ['email','profile'],
        code
    )

    print(credentials.id_token)

    return credentials.id_token

def get_id_token_with_code_method_2(code):

    token_endpoint = "https://oauth2.googleapis.com/token"
    payload = {
        'code': code,
        'client_id': config('CLIENT_ID'),
        'client_secret': config('CLIENT_SECRET'),
        'grant_type': 'authorization_code',
        'redirect_uri': "postmessage",
    }
    body = urllib.parse.urlencode(payload)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(token_endpoint,data = body,headers=headers)
    print(response,'response')
    
    if response.ok:   
        id_token = response.json()['id_token']
        print(id_token,'id_token')
        print(id_token)
        print(jwt.decode(id_token, options={"verify_signature": False}))
        return jwt.decode(id_token, options={"verify_signature": False})
    else:
        print(response.json()) 
        return None
