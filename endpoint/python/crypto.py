"""
Monocypher wrapper for encryption/decryption using crypto_lock/crypto_unlock
"""
import secrets
from typing import Tuple, Optional
import monocypher

def generate_key_pair() -> Tuple[bytes, bytes]:
    """Generate a public/private key pair using random bytes"""
    # Use monocypher's built-in key pair generation
    private_key, public_key = monocypher.generate_key_exchange_key_pair()
    return public_key, private_key

def encrypt(message: bytes, recipient_public_key: bytes, sender_private_key: bytes) -> bytes:
    """Encrypt message using crypto_lock"""
    nonce = secrets.token_bytes(24)
    
    # Perform key exchange to get shared key
    shared_key = monocypher.key_exchange(sender_private_key, recipient_public_key)
    
    # Use monocypher's lock function with shared key
    mac, ciphertext = monocypher.lock(shared_key, nonce, message)
    
    # Return nonce + mac + ciphertext
    return nonce + mac + ciphertext

def decrypt(encrypted_data: bytes, recipient_private_key: bytes, sender_public_key: bytes) -> Optional[bytes]:
    """Decrypt message using crypto_unlock"""
    if len(encrypted_data) < 40:  # 24 + 16 minimum
        return None
        
    nonce = encrypted_data[:24]
    mac = encrypted_data[24:40]
    ciphertext = encrypted_data[40:]
    
    try:
        # Perform key exchange to get shared key
        shared_key = monocypher.key_exchange(recipient_private_key, sender_public_key)
        
        # Use monocypher's unlock function with shared key
        plaintext = monocypher.unlock(shared_key, nonce, mac, ciphertext)
        return plaintext
    except Exception:
        return None