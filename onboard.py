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
import sys

# API credentials and base URL
API_ID = "<your api id here>"
API_KEY = "<your api key here>"
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
        "Request Method": method,
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
        debug_info["Response Headers"] = dict(response.headers)
        debug_info["Response Body"] = response.text
        
        if response.status_code not in [200, 201, 204]:
            error_log.append(debug_info)
        
        return response
    except requests.exceptions.RequestException as e:
        debug_info["Error"] = str(e)
        error_log.append(debug_info)
        return None

def check_api_connection():
    response = make_api_request("GET", "/ping")
    if response and response.status_code == 200:
        data = response.json()
        if data.get('result') == "Pong":
            print("API connection successful.")
            return True
    print("Error connecting to the API. Please contact hayden.loader@nextgen.group for assistance.")
    if error_log:
        print("Error details:")
        print(json.dumps(error_log, indent=2))
    return False

def get_user_email():
    response = make_api_request("GET", "/MasterPage")
    if response and response.status_code == 200:
        data = response.json()
        return data.get('user', {}).get('userEmail')
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

def invite_users(project_id, team_id, users):
    results = []
    for user in users:
        payload = {
            "email": user['email'],
            "firstName": user['first_name'],
            "lastName": user['last_name'],
            "projectId": project_id,
            "teamId": team_id,
            "userLevel": user['user_level'],
            "suppressEmails": False
        }
    
        response = make_api_request("POST", "/invitations/actions/inviteprojectmember", payload=payload)
    
        if response is None:
            print(f"No response received from the API for user {user['email']}. This could be due to a network issue or API downtime.")
            continue
    
        if response.status_code == 200:
            results.append(response.json())
        else:
            error_info = {
                "User": user['email'],
                "Status Code": response.status_code,
                "Response Content": response.text,
                "Request Payload": payload
            }
            error_log.append({
                "Error Type": "User Invitation Error",
                "Error Details": error_info
            })
            print(f"Invitation failed for user {user['email']}. Status code: {response.status_code}")
            print(f"Error message: {response.text}")

    return results if results else None

def get_policy_id(project_id):
    response = make_api_request("GET", f"/projects/{project_id}/policies")
    
    if response and response.status_code == 200:
        policies = response.json()
        if policies and len(policies) > 0:
            return policies[0]['id']
        else:
            print("No policies found for the project.")
    return None

def create_environment(customer_name, project_id, team_id, policy_id, owner_email):
    payload = {
        "environment": {
            "name": f"{customer_name} example environment",
            "projectId": project_id,
            "teamId": team_id,
            "policyId": policy_id,
            "regionId": "RE0YOUV7_lTmgb0X8D1UjM3g2",
            "description": "Example environment created for you by the CyberLAB team!",
            "externalCloudData": [],
            "OwnerEmail": owner_email
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
            default_user_level_count = 0
            for row in reader:
                if len(row) < 3 or not is_valid_email(row[0]):
                    print(f"Skipping invalid row: {row}")
                    continue
                user_level = int(row[3]) if len(row) > 3 and row[3] in ['2', '4', '8'] else 8
                if user_level == 8 and len(row) <= 3:
                    default_user_level_count += 1
                users.append({
                    'email': row[0],
                    'first_name': row[1],
                    'last_name': row[2],
                    'user_level': user_level
                })
        print(f"Successfully loaded {len(users)} users from the CSV file.")
        if default_user_level_count > 0:
            print(f"{default_user_level_count} users seen in the CSV do not have a user level defined and will be added as Project Managers.")
        return users
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

def get_user_level():
    while True:
        print("\nUser Levels:")
        print("2 - Team Member")
        print("4 - Team Manager")
        print("8 - Project Manager")
        level = input("Enter the user level (2, 4, or 8): ")
        if level in ['2', '4', '8']:
            return int(level)
        print("Invalid input. Please enter 2, 4, or 8.")

def get_users_input():
    users = []
    while True:
        email = input("Enter user's email address: ")
        if not is_valid_email(email):
            print("Invalid email address. Please try again.")
            continue
        first_name = input("Enter user's first name: ")
        last_name = input("Enter user's last name: ")
        user_level = get_user_level()
        users.append({
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'user_level': user_level
        })
        if input("Would you like to add another user? (y/n): ").lower() != 'y':
            break
    print(f"Successfully added {len(users)} users manually.")
    return users

def main():
    print("Starting the onboarding process...")

    if not check_api_connection():
        sys.exit(1)

    user_email = get_user_email()
    if not user_email:
        print("Failed to retrieve user email. Please contact hayden.loader@nextgen.group for assistance.")
        sys.exit(1)
    
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
        print(f"Successfully invited {len(invitation_data)} out of {len(users)} users.")
    else:
        print("Failed to invite users. The onboarding process is incomplete.")
        print("Please check the error log for more details.")
        return

    print("\nCreating the environment...")
    environment_data = create_environment(customer_name, project_id, team_id, policy_id, user_email)
    if environment_data:
        print("Environment created successfully.")
    else:
        print("Failed to create the environment. The onboarding process is incomplete.")

    if error_log:
        print("\nERROR LOG:")
        print("Errors occurred during the onboarding process. Please send the following error log to hayden.loader@nextgen.group:")
        for i, error in enumerate(error_log, 1):
            print(f"\nError {i}:")
            print(json.dumps(error, indent=2))
    else:
        print("\nThe onboarding process has completed successfully!")

    # Always display errors, even if the process was aborted
    if error_log:
        print("\nDetailed Error Log:")
        for i, error in enumerate(error_log, 1):
            print(f"\nError {i}:")
            print(json.dumps(error, indent=2))

if __name__ == "__main__":
    main()
