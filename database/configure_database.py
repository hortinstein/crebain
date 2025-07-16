import os
import time

import requests
from pocketbase import PocketBase
from dotenv import load_dotenv


# Environment variables
load_dotenv()
POCKETBASE_URL = os.getenv("POCKETBASE_URL", "http://localhost:8090/")  # Update with your PocketBase URL
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Define the collections schema
collections = [
    {
        "id": "_pb_ref_agents_",
        "name": "reference_agents",
        "type": "base",
        "schema": [
            {"name": "user_id", "type": "text", "required": False, "unique": False},
            {"name": "os", "type": "text", "required": False, "unique": False},
            {"name": "arch", "type": "text", "required": False, "unique": False},
            {"name": "file_info", "type": "json", "required": True, "unique": False,"options": {"maxSize": 5242880}},
            {"name": "build_id", "type": "text", "required": True, "unique": True},
            {"name": "enc_config", "type": "text", "required": False, "unique": False},
            {"name": "bin_size", "type": "number", "required": False, "unique": False},
            {"name": "word_list", "type": "file", "required": True, "unique": False,"options": {"maxSize": 5242880,"maxSelect":1}},
            {"name": "binary", "type": "file", "required": True, "unique": False,"options": {"maxSize": 5242880,"maxSelect":1}}
        ],
        "listRule": "@request.auth.id != \"\"",
        "viewRule": "@request.auth.id != \"\"",
    },
    {
        "id": "_pb_con_agents_",
        "name": "configured_agents",
        "type": "base",
        "schema": [
            {"name": "user_id", "type": "text", "required": False, "unique": False},
            {"name": "pb_reference_id", "type": "relation", "required": True, "unique": False,"options": {"collectionId": "_pb_ref_agents_","maxSelect":1}},
            {"name": "deploy_id", "type": "text", "required": False, "unique": True},
            {"name": "build_id", "type": "text", "required": False, "unique": False},
            {"name": "callsign", "type": "text", "required": False, "unique": False},
            {"name": "os", "type": "text", "required": False, "unique": False},
            {"name": "arch", "type": "text", "required": False, "unique": False},
            {"name": "callback_address", "type": "text", "required": False, "unique": False},
            {"name": "c2_pub_key", "type": "text", "required": False, "unique": False},
            {"name": "c2_priv_key", "type": "text", "required": False, "unique": False},
            {"name": "kill_date", "type": "date", "required": False, "unique": False},
            {"name": "interval", "type": "number", "required": False, "unique": False},
            {"name": "agent_pub_key", "type": "text", "required": False, "unique": False},
            {"name": "enc_config", "type": "text", "required": False, "unique": False},
            {"name": "binary", "type": "file", "required": False, "unique": False,"options": {"maxSize": 5242880,"maxSelect":1}}
        ],
        "listRule": "@request.auth.id != \"\"",
        "viewRule": "@request.auth.id != \"\"",
        "createRule": "@request.auth.id != \"\"",

    },
    {
        "id": "_pb_callbacks__",
        "name": "callbacks",
        "type": "base",
        "schema": [
            {"name": "pb_configured_agent_id", "type": "relation", "required": True, "unique": False,"options": {"collectionId": "_pb_con_agents_","maxSelect":1}},    
            {"name": "deploy_id", "type": "text", "required": False, "unique": False},
            {"name": "ip", "type": "text", "required": False, "unique": False},
            {"name": "external_ip", "type": "text", "required": False, "unique": False},
            {"name": "city", "type": "text", "required": False, "unique": False},
            {"name": "country", "type": "text", "required": False, "unique": False},
            {"name": "lat_long", "type": "text", "required": False, "unique": False},
            {"name": "country_emoji", "type": "text", "required": False, "unique": False},
            {"name": "hostname", "type": "text", "required": False, "unique": False},
            {"name": "os", "type": "text", "required": False, "unique": False},
            {"name": "arch", "type": "text", "required": False, "unique": False},
            {"name": "users", "type": "text", "required": False, "unique": False},
            {"name": "boot_time", "type": "number", "required": False, "unique": False},
            {"name": "transport_metadata", "type": "json", "required": False, "unique": False},
        ],
        "listRule": "@request.auth.id != \"\"",
        "viewRule": "@request.auth.id != \"\"",
    },
    # {
    #     "id": "_pb_agent_grp__",
        
    #     "name": "agent_group",
    #     "type": "base",
    #     "schema": [
    #         {"name": "user_id", "type": "text", "required": False, "unique": False},
    #         {"name": "owner_id", "type": "text", "required": True, "unique": False},
    #         {"name": "description", "type": "text", "required": False, "unique": False},
    #         {"name": "name", "type": "text", "required": False, "unique": False},
    #         {"name": "pb_members_id", "type": "relation", "required": True, "unique": False,"options": {"collectionId": "_pb_con_agents_","maxSelect":None}},    
    #     ]
    # },
    #  {
    #     "id": "_pb_grp_task___",
        
    #     "name": "group_task",
    #     "type": "base",
    #     "schema": [
    #         {"name": "user_id", "type": "text", "required": False, "unique": False},
    #         {"name": "owner_id", "type": "text", "required": True, "unique": False},
    #         {"name": "description", "type": "text", "required": False, "unique": False},
    #         {"name": "pb_configured_agent_id", "type": "relation", "required": True, "unique": False,"options": {"collectionId": "_pb_agent_grp__","maxSelect":None}},    
    #     ]
    # },
    {
        "id": "_pb_task_rec___",
        "name": "task_record",
        "type": "base",
        "schema": [
            {"name": "pb_callback_id", "type": "relation", "required": True, "unique": False,"options": {"collectionId": "_pb_callbacks__","maxSelect":1}},               
            {"name": "pb_configured_agent_id", "type": "relation", "required": True, "unique": False,"options": {"collectionId": "_pb_con_agents_","maxSelect":1}},    
            {"name": "task_id", "type": "text", "required": True, "unique": False},
            {"name": "completed_at", "type": "date", "required": False, "unique": False},
            {"name": "task_num", "type": "number", "required": False, "unique": False},
            {"name": "arg", "type": "text", "required": False, "unique": False},
            {"name": "resp", "type": "text", "required": False, "unique": False},
            {"name": "transport_metadata", "type": "json", "required": False, "unique": False}
        ],
        "listRule": "@request.auth.id != \"\"",
        "viewRule": "@request.auth.id != \"\"",
    },
    {
        "id": "_pb_tasking____",
        "name": "tasking",
        "type": "base",
        "schema": [
            {"name": "user_id", "type": "text", "required": False, "unique": False},
            {"name": "pb_configured_agent_id", "type": "relation", "required": True, "unique": False,"options": {"collectionId": "_pb_con_agents_","maxSelect":1}},    
            {"name": "pb_agent_task_recs", "type": "relation", "required": False, "unique": False,"options": {"collectionId": "_pb_task_rec___","maxSelect":None}},
            {"name": "description", "type": "text", "required": False, "unique": False},
            {"name": "starts_at", "type": "date", "required": False, "unique": False},
            {"name": "expires_at", "type": "date", "required": False, "unique": False},
            {"name": "completed", "type": "bool", "required": False, "unique": False},
            {"name": "max_executions", "type": "number", "required": True, "unique": False},
            {"name": "task", "type": "number", "required": False, "unique": False},
            {"name": "arg", "type": "text", "required": False, "unique": False}
        ],
        "listRule": "@request.auth.id != \"\"",
        "viewRule": "@request.auth.id != \"\"",
    },
]


# Authenticate with PocketBase
def authenticate(client):
    client.admins.auth_with_password(ADMIN_EMAIL,ADMIN_PASSWORD )

# Create or update collections
def create_collections(client):
    for collection in collections:
        try:
            result = client.collections.create(collection)
            print(f"Collection '{collection['name']}' created successfully: {result}")
        except Exception as e:
            print(f"Collection '{collection['name']}' failed to create: {e}")
            # Try to get more detailed error information
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Detailed error: {e.response.text}")
            elif hasattr(e, 'data'):
                print(f"Error data: {e.data}")
            # Try to delete existing collection and recreate
            try:
                client.collections.delete(collection['id'])
                print(f"Deleted existing collection '{collection['name']}'")
                result = client.collections.create(collection)
                print(f"Collection '{collection['name']}' recreated successfully: {result}")
            except Exception as e2:
                print(f"Failed to recreate collection '{collection['name']}': {e2}")
                if hasattr(e2, 'response') and hasattr(e2.response, 'text'):
                    print(f"Detailed recreate error: {e2.response.text}")
                elif hasattr(e2, 'data'):
                    print(f"Recreate error data: {e2.data}")


def remove_collections(client,name):
     # Fetch all records from the collection
    records = client.collection(name).get_list(1, 200)  # Adjust batch size if needed
    
    while records.items:
        for record in records.items:
            # Delete each record by its ID
            client.collection(name).delete(record.id)
            print(f"Deleted record with ID: {record.id}")
        
        # Fetch the next batch of records
        records = client.collection(name).get_list(1, 200)


if __name__ == "__main__":
    client = PocketBase(POCKETBASE_URL)

    # Authenticate and create collections
    authenticate(client)
    create_collections(client)