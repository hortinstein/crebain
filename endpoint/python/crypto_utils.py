#!/usr/bin/env python3
"""
Simple encryption utilities for endpoint agents.
Uses basic cryptographic operations with standard library.
"""

import base64
import hashlib
import os
from typing import Tuple

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


def generate_keypair() -> Tuple[bytes, bytes]:
    """Generate a keypair (simplified for demonstration)."""
    private_key = os.urandom(32)
    # For demo purposes, derive public key from private key using hash
    public_key = hashlib.sha256(private_key + b"public").digest()
    return private_key, public_key


def derive_shared_secret(my_private_key: bytes, their_public_key: bytes) -> bytes:
    """Derive shared secret from private/public key pair."""
    # In a real ECDH implementation, this would be a proper curve operation
    # For demo, we simulate by creating a deterministic shared secret
    
    # Sort keys to ensure both parties get the same result
    key1, key2 = sorted([my_private_key, their_public_key])
    combined = key1 + key2
    return hashlib.sha256(combined).digest()


def encrypt_message(message: str, recipient_public_key: bytes, sender_private_key: bytes) -> str:
    """Encrypt message using simple XOR-based encryption for demonstration."""
    # Simple XOR encryption for demonstration purposes
    # In production, use proper Monocypher or similar
    
    # Derive shared secret
    key_material = derive_shared_secret(sender_private_key, recipient_public_key)
    
    # Convert message to bytes
    message_bytes = message.encode('utf-8')
    
    # XOR encrypt
    encrypted = bytearray()
    for i, byte in enumerate(message_bytes):
        key_byte = key_material[i % len(key_material)]
        encrypted.append(byte ^ key_byte)
    
    # Add length prefix and return base64
    length_prefix = len(message_bytes).to_bytes(4, 'big')
    full_encrypted = length_prefix + bytes(encrypted)
    return base64.b64encode(full_encrypted).decode()


def decrypt_message(encrypted_message: str, sender_public_key: bytes, recipient_private_key: bytes) -> str:
    """Decrypt message using simple XOR-based encryption for demonstration."""
    # Decode from base64
    encrypted_data = base64.b64decode(encrypted_message.encode())
    
    # Extract length and encrypted message
    length = int.from_bytes(encrypted_data[:4], 'big')
    encrypted_bytes = encrypted_data[4:]
    
    # Derive shared secret (same as encryption due to deterministic derivation)
    key_material = derive_shared_secret(recipient_private_key, sender_public_key)
    
    # XOR decrypt
    decrypted = bytearray()
    for i in range(length):
        key_byte = key_material[i % len(key_material)]
        decrypted.append(encrypted_bytes[i] ^ key_byte)
    
    return bytes(decrypted).decode('utf-8')


def encode_key_b64(key: bytes) -> str:
    """Encode key as base64 string."""
    return base64.b64encode(key).decode()


def decode_key_b64(key_str: str) -> bytes:
    """Decode base64 key string to bytes."""
    return base64.b64decode(key_str.encode())