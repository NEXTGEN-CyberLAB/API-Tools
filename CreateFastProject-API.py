import requests
import time
import random
import string
import hashlib
import json

# Define the API endpoint and your API credentials
API_ID = "<your api id here>"
API_KEY = "<your api key here>"
URL = "https://use.cloudshare.com/api/v3/Projects/CreateFastProject"

# Generate timestamp and token
TIMESTAMP = str(int(time.time()))
TOKEN = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

# Create the HMAC signature
MESSAGE = f"{API_KEY}{URL}{TIMESTAMP}{TOKEN}"
HMAC = hashlib.sha1(MESSAGE.encode()).hexdigest()

# Construct the Authorization header
AUTH_PARAM = f"userapiid:{API_ID};timestamp:{TIMESTAMP};token:{TOKEN};hmac:{HMAC}"
AUTH_HEADER = f"cs_sha1 {AUTH_PARAM}"

# Define the payload
PAYLOAD = {
    "subscriptionId": "SBPnwD_kw-0hN_O5bhUwKTVQ2",
    "projectName": "<your project name here>",
    "teamNames": ["<your team name here>"],
    "projectType": 0
}

# Make the POST request to create a project
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": AUTH_HEADER
}

try:
    response = requests.post(URL, headers=headers, json=PAYLOAD, verify=True)
    
    # Print only the status code and response body
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
    
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")