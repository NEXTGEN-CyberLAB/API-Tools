#!/bin/bash

# Define the API endpoint and your API credentials
API_ID="<your api id here>"
API_KEY="<your api key here>"
URL="https://use.cloudshare.com/api/v3/Projects/CreateFastProject"

# Generate timestamp and token
TIMESTAMP=$(date +%s)
TOKEN=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 10 ; echo '')

# Create the HMAC signature
MESSAGE="${API_KEY}${URL}${TIMESTAMP}${TOKEN}"
HMAC=$(echo -n "$MESSAGE" | sha1sum | awk '{print $1}')

# Construct the Authorization header
AUTH_PARAM="userapiid:$API_ID;timestamp:$TIMESTAMP;token:$TOKEN;hmac:$HMAC"
AUTH_HEADER="cs_sha1 $AUTH_PARAM"

# Define the payload
PAYLOAD='{
  "subscriptionId": "SBPnwD_kw-0hN_O5bhUwKTVQ2",
  "projectName": "<your project name here>",
  "teamNames": ["<your team name here>"],
  "projectType": 0
}'

# Make the POST request to create a project with verbose output and proper SSL verification
curl -X POST "$URL" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: $AUTH_HEADER" \
  -d "$PAYLOAD" \
  --cacert /etc/ssl/certs/ca-certificates.crt