#!/usr/bin/env python3
"""
Configuration management for 528-byte embedded agent config.
Layout: 128 bytes keypair + 400 bytes JSON config
"""

import json
import struct
from typing import Dict, Any, Tuple

from crypto_utils import decode_key_b64, encode_key_b64


CONFIG_SIZE = 528
KEYPAIR_SIZE = 128  # 64 bytes pub + 64 bytes priv
JSON_SIZE = 400

# Sample configuration for testing
SAMPLE_CONFIG = {
    "build_id": "test_build_001",
    "deploy_id": "test_deploy_001", 
    "kill_epoch": "1764091654",
    "interval": "5000",
    "callback": "http://localhost:8080/callback",
    "c2_pub_key": "",  # Will be filled by generate_sample_config
    "agent_priv_key": "",  # Will be filled by generate_sample_config
    "filler": ""  # Will be padded to exact size
}


def pad_json_to_size(config_dict: Dict[str, Any], target_size: int) -> str:
    """Pad JSON config to exact target size with filler field."""
    config_copy = config_dict.copy()
    
    # Calculate current size without filler
    config_copy["filler"] = ""
    current_json = json.dumps(config_copy, separators=(',', ':'))
    current_size = len(current_json)
    
    if current_size > target_size:
        raise ValueError(f"Config too large: {current_size} > {target_size}")
    
    # Calculate filler needed
    filler_size = target_size - current_size
    if filler_size > 0:
        # Account for the filler field quotes and content
        # We need: "filler":"X" where X is the padding
        filler_overhead = len('"filler":""')
        actual_filler_size = filler_size - filler_overhead
        if actual_filler_size > 0:
            config_copy["filler"] = "X" * actual_filler_size
    
    final_json = json.dumps(config_copy, separators=(',', ':'))
    
    # Ensure exact size
    if len(final_json) < target_size:
        padding_needed = target_size - len(final_json)
        config_copy["filler"] += "X" * padding_needed
        final_json = json.dumps(config_copy, separators=(',', ':'))
    elif len(final_json) > target_size:
        # Trim filler if needed
        excess = len(final_json) - target_size
        current_filler = config_copy["filler"]
        config_copy["filler"] = current_filler[:-excess] if len(current_filler) >= excess else ""
        final_json = json.dumps(config_copy, separators=(',', ':'))
    
    return final_json


def pack_config(pub_key: bytes, priv_key: bytes, config_dict: Dict[str, Any]) -> bytes:
    """Pack keypair and config into 528-byte binary format."""
    if len(pub_key) != 32:
        raise ValueError(f"Public key must be 32 bytes, got {len(pub_key)}")
    if len(priv_key) != 32:
        raise ValueError(f"Private key must be 32 bytes, got {len(priv_key)}")
    
    # Pad keys to 64 bytes each (Monocypher format)
    pub_key_padded = pub_key + b'\x00' * (64 - len(pub_key))
    priv_key_padded = priv_key + b'\x00' * (64 - len(priv_key))
    
    # Pack JSON config to exact size
    json_config = pad_json_to_size(config_dict, JSON_SIZE)
    json_bytes = json_config.encode('utf-8')
    
    if len(json_bytes) != JSON_SIZE:
        raise ValueError(f"JSON config must be exactly {JSON_SIZE} bytes, got {len(json_bytes)}")
    
    # Combine all parts
    config_data = pub_key_padded + priv_key_padded + json_bytes
    
    if len(config_data) != CONFIG_SIZE:
        raise ValueError(f"Total config must be exactly {CONFIG_SIZE} bytes, got {len(config_data)}")
    
    return config_data


def unpack_config(config_data: bytes) -> Tuple[bytes, bytes, Dict[str, Any]]:
    """Unpack 528-byte binary config into keypair and JSON."""
    if len(config_data) != CONFIG_SIZE:
        raise ValueError(f"Config data must be exactly {CONFIG_SIZE} bytes, got {len(config_data)}")
    
    # Extract components
    pub_key_padded = config_data[:64]
    priv_key_padded = config_data[64:128]
    json_bytes = config_data[128:]
    
    # Remove padding from keys (take first 32 bytes)
    pub_key = pub_key_padded[:32]
    priv_key = priv_key_padded[:32]
    
    # Parse JSON config
    try:
        json_str = json_bytes.decode('utf-8').rstrip('\x00')
        config_dict = json.loads(json_str)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError(f"Failed to parse JSON config: {e}")
    
    return pub_key, priv_key, config_dict


def generate_sample_config(c2_pub_key: bytes, agent_priv_key: bytes, agent_pub_key: bytes) -> bytes:
    """Generate a sample 528-byte configuration for testing."""
    config = SAMPLE_CONFIG.copy()
    config["c2_pub_key"] = encode_key_b64(c2_pub_key)
    config["agent_priv_key"] = encode_key_b64(agent_priv_key)
    
    return pack_config(agent_pub_key, agent_priv_key, config)