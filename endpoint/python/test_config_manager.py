#!/usr/bin/env python3
"""
Unit tests for config_manager module.
"""

import unittest
import json

from config_manager import (
    pack_config,
    unpack_config,
    generate_sample_config,
    pad_json_to_size,
    SAMPLE_CONFIG,
    CONFIG_SIZE,
    KEYPAIR_SIZE,
    JSON_SIZE
)
from crypto_utils import generate_keypair, encode_key_b64


class TestConfigManager(unittest.TestCase):
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.agent_priv, self.agent_pub = generate_keypair()
        self.c2_priv, self.c2_pub = generate_keypair()
        
        self.test_config = {
            "build_id": "test_build_001",
            "deploy_id": "test_deploy_001",
            "kill_epoch": "1764091654",
            "interval": "5000",
            "callback": "http://localhost:8080/callback",
            "c2_pub_key": encode_key_b64(self.c2_pub),
            "agent_priv_key": encode_key_b64(self.agent_priv),
            "filler": ""
        }
    
    def test_pad_json_to_size(self) -> None:
        """Test JSON padding to exact size."""
        padded_json = pad_json_to_size(self.test_config, JSON_SIZE)
        
        self.assertEqual(len(padded_json), JSON_SIZE)
        
        # Should be valid JSON
        parsed = json.loads(padded_json)
        self.assertIsInstance(parsed, dict)
        self.assertIn("filler", parsed)
    
    def test_pack_unpack_config_roundtrip(self) -> None:
        """Test packing and unpacking configuration."""
        # Pack configuration
        packed = pack_config(self.agent_pub, self.agent_priv, self.test_config)
        
        self.assertEqual(len(packed), CONFIG_SIZE)
        
        # Unpack configuration
        unpacked_pub, unpacked_priv, unpacked_config = unpack_config(packed)
        
        # Verify keys match
        self.assertEqual(unpacked_pub, self.agent_pub)
        self.assertEqual(unpacked_priv, self.agent_priv)
        
        # Verify config fields match (excluding filler)
        for key in self.test_config:
            if key != "filler":
                self.assertEqual(unpacked_config[key], self.test_config[key])
    
    def test_generate_sample_config(self) -> None:
        """Test sample configuration generation."""
        config_data = generate_sample_config(self.c2_pub, self.agent_priv, self.agent_pub)
        
        self.assertEqual(len(config_data), CONFIG_SIZE)
        
        # Unpack and verify
        unpacked_pub, unpacked_priv, unpacked_config = unpack_config(config_data)
        
        self.assertEqual(unpacked_pub, self.agent_pub)
        self.assertEqual(unpacked_priv, self.agent_priv)
        self.assertEqual(unpacked_config["c2_pub_key"], encode_key_b64(self.c2_pub))
        self.assertEqual(unpacked_config["agent_priv_key"], encode_key_b64(self.agent_priv))
    
    def test_config_size_validation(self) -> None:
        """Test configuration size validation."""
        # Test with wrong key sizes
        short_key = b"short"
        
        with self.assertRaises(ValueError):
            pack_config(short_key, self.agent_priv, self.test_config)
        
        with self.assertRaises(ValueError):
            pack_config(self.agent_pub, short_key, self.test_config)
    
    def test_unpack_invalid_config(self) -> None:
        """Test unpacking invalid configuration data."""
        # Test with wrong size
        invalid_data = b"invalid" * 10
        
        with self.assertRaises(ValueError):
            unpack_config(invalid_data)
    
    def test_config_fields_present(self) -> None:
        """Test that all required configuration fields are present."""
        config_data = generate_sample_config(self.c2_pub, self.agent_priv, self.agent_pub)
        _, _, config = unpack_config(config_data)
        
        required_fields = [
            "build_id", "deploy_id", "kill_epoch", "interval",
            "callback", "c2_pub_key", "agent_priv_key"
        ]
        
        for field in required_fields:
            self.assertIn(field, config)
            self.assertIsInstance(config[field], str)
            self.assertNotEqual(config[field], "")
    
    def test_json_size_exactly_400_bytes(self) -> None:
        """Test that JSON configuration is exactly 400 bytes."""
        padded_json = pad_json_to_size(self.test_config, JSON_SIZE)
        
        self.assertEqual(len(padded_json.encode('utf-8')), JSON_SIZE)
    
    def test_keypair_size_exactly_128_bytes(self) -> None:
        """Test that keypair section is exactly 128 bytes."""
        config_data = generate_sample_config(self.c2_pub, self.agent_priv, self.agent_pub)
        
        # Extract keypair section
        keypair_section = config_data[:KEYPAIR_SIZE]
        
        self.assertEqual(len(keypair_section), KEYPAIR_SIZE)
    
    def test_sample_config_structure(self) -> None:
        """Test sample configuration has correct structure."""
        self.assertIsInstance(SAMPLE_CONFIG, dict)
        self.assertIn("build_id", SAMPLE_CONFIG)
        self.assertIn("deploy_id", SAMPLE_CONFIG)
        self.assertIn("kill_epoch", SAMPLE_CONFIG)
        self.assertIn("interval", SAMPLE_CONFIG)
        self.assertIn("callback", SAMPLE_CONFIG)
        self.assertIn("c2_pub_key", SAMPLE_CONFIG)
        self.assertIn("agent_priv_key", SAMPLE_CONFIG)
        self.assertIn("filler", SAMPLE_CONFIG)


if __name__ == '__main__':
    unittest.main()