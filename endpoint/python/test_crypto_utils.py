#!/usr/bin/env python3
"""
Unit tests for crypto_utils module.
"""

import unittest
import base64

from crypto_utils import (
    generate_keypair,
    derive_shared_secret,
    encrypt_message,
    decrypt_message,
    encode_key_b64,
    decode_key_b64
)


class TestCryptoUtils(unittest.TestCase):
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.alice_priv, self.alice_pub = generate_keypair()
        self.bob_priv, self.bob_pub = generate_keypair()
        self.test_message = "Hello, World!"
    
    def test_generate_keypair(self) -> None:
        """Test keypair generation."""
        priv_key, pub_key = generate_keypair()
        
        self.assertEqual(len(priv_key), 32)
        self.assertEqual(len(pub_key), 32)
        self.assertNotEqual(priv_key, pub_key)
    
    def test_derive_shared_secret(self) -> None:
        """Test shared secret derivation."""
        # Test that shared secret is deterministic
        secret1 = derive_shared_secret(self.alice_priv, self.bob_pub)
        secret2 = derive_shared_secret(self.alice_priv, self.bob_pub)
        
        self.assertEqual(secret1, secret2)
        self.assertEqual(len(secret1), 32)
        
        # Test that different key pairs produce different secrets
        charlie_priv, charlie_pub = generate_keypair()
        secret3 = derive_shared_secret(self.alice_priv, charlie_pub)
        self.assertNotEqual(secret1, secret3)
    
    def test_encrypt_decrypt_roundtrip(self) -> None:
        """Test encryption and decryption roundtrip."""
        # Alice encrypts message for Bob
        encrypted = encrypt_message(self.test_message, self.bob_pub, self.alice_priv)
        
        # Bob decrypts message from Alice
        decrypted = decrypt_message(encrypted, self.alice_pub, self.bob_priv)
        
        self.assertEqual(decrypted, self.test_message)
    
    def test_encrypt_decrypt_different_keys(self) -> None:
        """Test that decryption fails with wrong keys."""
        charlie_priv, charlie_pub = generate_keypair()
        
        # Alice encrypts message for Bob
        encrypted = encrypt_message(self.test_message, self.bob_pub, self.alice_priv)
        
        # Charlie tries to decrypt (should fail)
        with self.assertRaises(Exception):
            decrypt_message(encrypted, self.alice_pub, charlie_priv)
    
    def test_encode_decode_key_b64(self) -> None:
        """Test base64 key encoding/decoding."""
        encoded = encode_key_b64(self.alice_pub)
        decoded = decode_key_b64(encoded)
        
        self.assertEqual(decoded, self.alice_pub)
        self.assertIsInstance(encoded, str)
        self.assertIsInstance(decoded, bytes)
    
    def test_empty_message_encryption(self) -> None:
        """Test encryption of empty message."""
        empty_message = ""
        encrypted = encrypt_message(empty_message, self.bob_pub, self.alice_priv)
        decrypted = decrypt_message(encrypted, self.alice_pub, self.bob_priv)
        
        self.assertEqual(decrypted, empty_message)
    
    def test_large_message_encryption(self) -> None:
        """Test encryption of large message."""
        large_message = "X" * 10000
        encrypted = encrypt_message(large_message, self.bob_pub, self.alice_priv)
        decrypted = decrypt_message(encrypted, self.alice_pub, self.bob_priv)
        
        self.assertEqual(decrypted, large_message)
    
    def test_json_message_encryption(self) -> None:
        """Test encryption of JSON formatted message."""
        json_message = '{"task_id": "test", "task_num": "1", "task_arg": "echo hello"}'
        encrypted = encrypt_message(json_message, self.bob_pub, self.alice_priv)
        decrypted = decrypt_message(encrypted, self.alice_pub, self.bob_priv)
        
        self.assertEqual(decrypted, json_message)


if __name__ == '__main__':
    unittest.main()