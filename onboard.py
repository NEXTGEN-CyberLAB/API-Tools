import requests
import time
import random
import string
import hashlib
import json
import urllib.parse

# Define the API endpoint and your API credentials
API_ID = "<your-API-ID-here>"
API_KEY = "<your-API-Key-here>"
BASE_URL = "https://use.cloudshare.com/api/v3"

def generate_auth_header(method, url, params=None):
    timestamp = str(int(time.time()))
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    
    if method == 'GET' and params:
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        full_url = f"{url}?{query_string}"
    else:
        full_url = url
    
    message = f"{API_KEY}{full_url}{timestamp}{token}"
    hmac = hashlib.sha1(message.encode()).hexdigest()
    auth_param = f"userapiid:{API_ID};timestamp:{timestamp};token:{token};hmac:{hmac}"
    return f"cs_sha1 {auth_param}"

def make_api_request(method, endpoint, params=None, payload=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": generate_auth_header(method, url, params)
    }
    
    # print(f"Request URL: {url}")
    # print(f"Request Headers: {headers}")
    # if payload:
    #     print(f"Request Payload: {json.dumps(payload, indent=2)}")
    # if params:
    #     print(f"Request Params: {params}")
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params, verify=True)
        else:
            response = requests.post(url, headers=headers, json=payload, verify=True)
        
        # print(f"Status Code: {response.status_code}")
        # print(f"Response Body: {response.text}")
        return response
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def create_project(customer_name):
    payload = {
        "subscriptionId": "SBPnwD_kw-0hN_O5bhUwKTVQ2",
        "projectName": f"test-NEXTGEN CyberLAB - {customer_name}",
        "teamNames": [customer_name],
        "projectType": 0
    }
    
    response = make_api_request("POST", "/Projects/CreateFastProject", payload=payload)
    
    if response and response.status_code == 200:
        data = response.json()
        if data.get('id'):
            return data
        else:
            print(f"Project creation failed: {data.get('message', 'Unknown error')}")
    return None

def get_team_id(project_id):
    params = {
        "getRows": "true",
        "projectId": project_id,
        "skip": "0"
    }
    
    response = make_api_request("GET", "/teams", params=params)
    
    if response and response.status_code == 200:
        data = response.json()
        if data.get('rows') and len(data['rows']) > 0:
            return data['rows'][0]['id']
        else:
            print("No team found for the project.")
    return None

def invite_user(email, first_name, last_name, project_id, team_id):
    payload = {
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "projectId": project_id,
        "teamId": team_id,
        "userLevel": 8,  # Project Manager
        "suppressEmails": False
    }
    
    response = make_api_request("POST", "/invitations/actions/inviteprojectmember", payload=payload)
    
    if response and response.status_code == 200:
        return response.json()
    else:
        print(f"Invitation failed: {response.json().get('message', 'Unknown error') if response else 'No response'}")
        return None

def get_policy_id(project_id):
    response = make_api_request("GET", f"/projects/{project_id}/policies")
    
    if response and response.status_code == 200:
        policies = response.json()
        if policies and len(policies) > 0:
            return policies[0]['id']
        else:
            print("No policies found for the project.")
    return None

def create_environment(customer_name, project_id, team_id, policy_id):
    payload = {
        "environment": {
            "name": f"{customer_name} example environment",
            "projectId": project_id,
            "teamId": team_id,
            "policyId": policy_id,
            "regionId": "RE0YOUV7_lTmgb0X8D1UjM3g2",
            "description": "Example environment created for you by the CyberLAB team!",
            "externalCloudData": [],
            "OwnerEmail": "hayden.loader@nextgen.group"
        },
        "preview": False,
        "itemsCart": [
            {
                "type": 2,
                "name": "Windows Server 2022 Standard",
                "description": "Windows Server 2022 Standard\r\n",
                "chocolateyPackages": [],
                "templateVmId": "VMQ8CMFMPg3qODIkjbyiIaQQ2"
            },
            {
                "type": 2,
                "name": "Ubuntu 22.04 LTS Desktop",
                "description": "Ubuntu 22.04 LTS Desktop",
                "chocolateyPackages": [],
                "templateVmId": "VMCuJ5pfZ_5buGrUxy-X7UYw2"
            },
            {
                "type": 2,
                "name": "Kali Linux 2022",
                "description": "Kali Linux 2022",
                "chocolateyPackages": [],
                "templateVmId": "VM4v4vMNJyot3DJgZk0Z9hYQ2"
            },
            {
                "type": 2,
                "name": "CentOS 8 Server",
                "description": "CentOS 8 Server",
                "chocolateyPackages": [],
                "templateVmId": "VMir6RBYieEi0OvNCHsQ52_g2"
            }
        ],
        "enableAutomaticSnapshot": False
    }
    
    response = make_api_request("POST", "/envs", payload=payload)
    
    if response and response.status_code == 200:
        return response.json()
    else:
        print(f"Environment creation failed: {response.json().get('message', 'Unknown error') if response else 'No response'}")
        return None

def main():
    print("Starting onboarding process...")
    
    customer_name = input("Enter customer name: ")
    first_name = input("Enter user's first name: ")
    last_name = input("Enter user's last name: ")
    email = input("Enter user's email address: ")

    print("\nCreating project...")
    project_data = create_project(customer_name)
    if not project_data or 'id' not in project_data:
        print("Failed to create project. Aborting onboarding process.")
        return

    project_id = project_data['id']
    print(f"Project created successfully. Project ID: {project_id}")

    print("\nFetching team ID...")
    team_id = get_team_id(project_id)
    if not team_id:
        print("Failed to fetch team ID. Aborting onboarding process.")
        return

    print(f"Team ID fetched successfully. Team ID: {team_id}")

    print("\nFetching policy ID...")
    policy_id = get_policy_id(project_id)
    if not policy_id:
        print("Failed to fetch policy ID. Aborting onboarding process.")
        return

    print(f"Policy ID fetched successfully. Policy ID: {policy_id}")

    print("\nInviting user...")
    invitation_data = invite_user(email, first_name, last_name, project_id, team_id)
    if invitation_data:
        print("User invited successfully as Project Manager.")
        # print(f"Invitation details: {json.dumps(invitation_data, indent=2)}")
    else:
        print("Failed to invite user. Onboarding process incomplete.")
        return

    print("\nCreating environment...")
    environment_data = create_environment(customer_name, project_id, team_id, policy_id)
    if environment_data:
        print("Environment created successfully.")
        # print(f"Environment details: {json.dumps(environment_data, indent=2)}")
    else:
        print("Failed to create environment. Onboarding process incomplete.")

    print("\nOnboarding process completed successfully!")

if __name__ == "__main__":
    main()