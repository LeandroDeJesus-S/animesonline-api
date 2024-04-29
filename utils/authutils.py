import os
from dotenv import load_dotenv
load_dotenv()

def validate_auth(headers):
    token = headers.get('X-Access-Token')
    if token != os.getenv('SECRET_KEY'):
        return False
    return True
