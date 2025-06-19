#!/usr/bin/env python3
"""
Simple demo test to verify basic functionality.
"""

from config_manager import generate_sample_config, unpack_config
from crypto_utils import generate_keypair
from agent import execute_command

def test_basic_functionality():
    """Test basic agent functionality without encryption."""
    
    print("Testing basic functionality...")
    
    # Test command execution
    result = execute_command("echo hello")
    print(f"Command execution result: '{result}'")
    assert result == "hello", f"Expected 'hello', got '{result}'"
    
    # Test configuration generation and parsing
    c2_priv, c2_pub = generate_keypair()
    agent_priv, agent_pub = generate_keypair()
    
    config_data = generate_sample_config(c2_pub, agent_priv, agent_pub)
    print(f"Config data size: {len(config_data)} bytes")
    assert len(config_data) == 528, f"Expected 528 bytes, got {len(config_data)}"
    
    # Test unpacking
    unpacked_pub, unpacked_priv, config = unpack_config(config_data)
    print(f"Unpacked config deploy_id: {config['deploy_id']}")
    print(f"Unpacked config callback: {config['callback']}")
    
    assert unpacked_pub == agent_pub
    assert unpacked_priv == agent_priv
    assert config['deploy_id'] == 'test_deploy_001'
    
    print("✅ All basic tests passed!")

if __name__ == '__main__':
    test_basic_functionality()