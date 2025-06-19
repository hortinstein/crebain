#!/usr/bin/env python3
"""
Integration test runner for all endpoint implementations.
Configures and tests each endpoint agent implementation.
"""

import json
import os
import sys
import tempfile
from typing import Dict, Any

# Add python directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from crypto_utils import generate_keypair, encode_key_b64
from config_manager import generate_sample_config


def create_sample_agent_config(output_file: str) -> Dict[str, Any]:
    """Create sample agent configuration file for testing."""
    # Generate keypairs
    c2_priv, c2_pub = generate_keypair()
    agent_priv, agent_pub = generate_keypair()
    
    # Generate configuration
    config_data = generate_sample_config(c2_pub, agent_priv, agent_pub)
    
    # Write to file
    with open(output_file, 'wb') as f:
        f.write(config_data)
    
    # Return keys for server config
    return {
        'c2_private_key': encode_key_b64(c2_priv),
        'c2_public_key': encode_key_b64(c2_pub),
        'agent_public_key': encode_key_b64(agent_pub),
        'agent_private_key': encode_key_b64(agent_priv)
    }


def create_server_config(keys: Dict[str, Any], output_file: str) -> None:
    """Create server configuration file for testing."""
    server_config = {
        "c2_priv_key": keys['c2_private_key'],
        "c2_pub_key": keys['c2_public_key'],
        "agent_pub_key": keys['agent_public_key'],
        "agent_priv_key": keys['agent_private_key']
    }
    
    with open(output_file, 'w') as f:
        json.dump(server_config, f, indent=2)


def test_python_endpoint() -> bool:
    """Test Python endpoint implementation."""
    print("Testing Python endpoint...")
    
    try:
        # Import and run Python tests
        from test_python_endpoint import run_integration_tests
        return run_integration_tests()
    except ImportError as e:
        print(f"Failed to import Python test module: {e}")
        return False
    except Exception as e:
        print(f"Python endpoint test failed: {e}")
        return False


def generate_test_configs() -> bool:
    """Generate test configuration files."""
    print("Generating test configuration files...")
    
    try:
        # Generate agent config
        agent_config_file = os.path.join(os.path.dirname(__file__), 'agent_config.bin')
        keys = create_sample_agent_config(agent_config_file)
        
        # Generate server config
        server_config_file = os.path.join(os.path.dirname(__file__), 'server_config.json')
        create_server_config(keys, server_config_file)
        
        print(f"Generated agent config: {agent_config_file} (528 bytes)")
        print(f"Generated server config: {server_config_file}")
        
        # Verify file sizes
        agent_size = os.path.getsize(agent_config_file)
        if agent_size != 528:
            print(f"Warning: Agent config size is {agent_size} bytes, expected 528")
            return False
        
        return True
        
    except Exception as e:
        print(f"Failed to generate test configs: {e}")
        return False


def run_unit_tests() -> bool:
    """Run unit tests for Python implementation."""
    print("Running Python unit tests...")
    
    try:
        import unittest
        import sys
        
        # Add python directory to path
        python_dir = os.path.join(os.path.dirname(__file__), '..', 'python')
        sys.path.insert(0, python_dir)
        
        # Import test modules
        import test_crypto_utils
        import test_config_manager
        import test_agent
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add test cases
        suite.addTests(loader.loadTestsFromModule(test_crypto_utils))
        suite.addTests(loader.loadTestsFromModule(test_config_manager))
        suite.addTests(loader.loadTestsFromModule(test_agent))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except Exception as e:
        print(f"Unit tests failed: {e}")
        return False


def main() -> None:
    """Main test runner."""
    print("=" * 60)
    print("Endpoint Agent Integration Test Suite")
    print("=" * 60)
    
    all_passed = True
    
    # Generate test configurations
    if not generate_test_configs():
        print("❌ Failed to generate test configurations")
        all_passed = False
    else:
        print("✅ Test configurations generated successfully")
    
    print()
    
    # Run unit tests
    if not run_unit_tests():
        print("❌ Unit tests failed")
        all_passed = False
    else:
        print("✅ Unit tests passed")
    
    print()
    
    # Test Python endpoint
    if not test_python_endpoint():
        print("❌ Python endpoint tests failed")
        all_passed = False
    else:
        print("✅ Python endpoint tests passed")
    
    print()
    print("=" * 60)
    
    if all_passed:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()