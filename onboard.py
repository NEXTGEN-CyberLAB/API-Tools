import requests
import time
import random
import string
import hashlib
import json
import urllib.parse
import csv
import os
import re

# API credentials and base URL
API_ID = "<your-API-ID-here>"
API_KEY = "<your-API-Key-here>"
BASE_URL = "https://use.cloudshare.com/api/v3"

error_log = []

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
    
    debug_info = {
        "Request URL": url,
        "Request Headers": headers,
        "Request Payload": payload,
        "Request Params": params
    }
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params, verify=True)
        else:
            response = requests.post(url, headers=headers, json=payload, verify=True)
        
        debug_info["Status Code"] = response.status_code
        debug_info["Response Body"] = response.text
        
        if response.status_code not in [200, 201, 204]:
            error_log.append(debug_info)
        
        return response
    except requests.exceptions.RequestException as e:
        debug_info["Error"] = str(e)
        error_log.append(debug_info)
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
        "userLevel": 8,
        "suppressEmails": False
    }
    
    response = make_api_request("POST", "/invitations/actions/inviteprojectmember", payload=payload)
    
    if response and response.status_code == 200:
        return response.json()
    else:
        print(f"Invitation failed for {email}: {response.json().get('message', 'Unknown error') if response else 'No response'}")
        return None

def invite_users(project_id, team_id, users):
    results = []
    for user in users:
        result = invite_user(user['email'], user['first_name'], user['last_name'], project_id, team_id)
        if result:
            results.append(result)
        else:
            print(f"Failed to invite user: {user['email']}")
    return results

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

def is_valid_email(email):
    # Updated regex pattern to allow '+' in the local part of the email
    pattern = r'^[\w\.-]+(\+[\w\.-]+)?@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def load_users_from_csv():
    file_path = 'users.csv'
    if not os.path.exists(file_path):
        print("users.csv not found in the current directory.")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.reader(csvfile)
            users = []
            for row in reader:
                if len(row) != 3 or not is_valid_email(row[0]):
                    print(f"Skipping invalid row: {row}")
                    continue
                users.append({
                    'email': row[0],
                    'first_name': row[1],
                    'last_name': row[2]
                })
        print(f"Successfully loaded {len(users)} users from the CSV file.")
        return users
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

def get_users_input():
    users = []
    while True:
        email = input("Enter user's email address: ")
        if not is_valid_email(email):
            print("Invalid email address. Please try again.")
            continue
        first_name = input("Enter user's first name: ")
        last_name = input("Enter user's last name: ")
        users.append({
            'email': email,
            'first_name': first_name,
            'last_name': last_name
        })
        if input("Would you like to add another user? (y/n): ").lower() != 'y':
            break
    print(f"Successfully added {len(users)} users manually.")
    return users

def main():
    print("Starting the onboarding process...")
    
    customer_name = input("Enter the customer name: ")

    users = load_users_from_csv()
    if users:
        use_csv = input("users.csv file found. Would you like to use the users detailed in this file? (y/n): ").lower() == 'y'
        if not use_csv:
            users = None

    while users is None:
        users = get_users_input()
        if not users:
            retry = input("No users were added. Would you like to try again? (y/n): ").lower()
            if retry != 'y':
                print("Aborting the onboarding process.")
                return

    print("\nCreating the project...")
    project_data = create_project(customer_name)
    if not project_data or 'id' not in project_data:
        print("Failed to create the project. Aborting the onboarding process.")
        return

    project_id = project_data['id']
    print(f"Project created successfully. Project ID: {project_id}")

    print("\nFetching the team ID...")
    team_id = get_team_id(project_id)
    if not team_id:
        print("Failed to fetch the team ID. Aborting the onboarding process.")
        return

    print(f"Team ID fetched successfully. Team ID: {team_id}")

    print("\nFetching the policy ID...")
    policy_id = get_policy_id(project_id)
    if not policy_id:
        print("Failed to fetch the policy ID. Aborting the onboarding process.")
        return

    print(f"Policy ID fetched successfully. Policy ID: {policy_id}")

    print("\nInviting users...")
    invitation_data = invite_users(project_id, team_id, users)
    if invitation_data:
        print(f"Successfully invited {len(invitation_data)} out of {len(users)} users as Project Managers.")
    else:
        print("Failed to invite any users. The onboarding process is incomplete.")
        return

    print("\nCreating the environment...")
    environment_data = create_environment(customer_name, project_id, team_id, policy_id)
    if environment_data:
        print("Environment created successfully.")
    else:
        print("Failed to create the environment. The onboarding process is incomplete.")

    if error_log:
        print("\nERROR LOG:")
        print("Errors occurred during the onboarding process. Please send the following error log to hayden.loader@nextgen.group:")
        print(json.dumps(error_log, indent=2))
    else:
        print("\nThe onboarding process has completed successfully!")

if __name__ == "__main__":
    main()
