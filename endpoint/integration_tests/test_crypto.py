"""
Integration tests for monocypher crypto functions
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'python'))

from crypto import generate_key_pair, encrypt, decrypt

def test_key_generation():
    """Test key pair generation"""
    public_key, private_key = generate_key_pair()
    
    assert len(public_key) == 32, f"Public key wrong size: {len(public_key)}"
    assert len(private_key) == 32, f"Private key wrong size: {len(private_key)}"
    assert public_key != private_key, "Keys should not be identical"
    
    print("✓ Key generation test passed")

def test_encrypt_decrypt():
    """Test encryption and decryption"""
    # Generate two key pairs
    alice_pub, alice_priv = generate_key_pair()
    bob_pub, bob_priv = generate_key_pair()
    
    # Test message
    message = b"Hello, World! This is a test message."
    
    # Alice encrypts for Bob
    encrypted = encrypt(message, bob_pub, alice_priv)
    assert len(encrypted) > len(message), "Encrypted data should be longer"
    
    # Bob decrypts from Alice
    decrypted = decrypt(encrypted, bob_priv, alice_pub)
    assert decrypted == message, f"Decryption failed: {decrypted} != {message}"
    
    print("✓ Encrypt/decrypt test passed")

def test_decrypt_failure():
    """Test decryption with wrong keys fails"""
    alice_pub, alice_priv = generate_key_pair()
    bob_pub, bob_priv = generate_key_pair()
    charlie_pub, charlie_priv = generate_key_pair()
    
    message = b"Secret message"
    encrypted = encrypt(message, bob_pub, alice_priv)
    
    # Charlie tries to decrypt (should fail)
    decrypted = decrypt(encrypted, charlie_priv, alice_pub)
    assert decrypted is None, "Decryption should fail with wrong key"
    
    print("✓ Decrypt failure test passed")

def test_configuration_crypto():
    """Test crypto with sample configuration"""
    from configure import create_config, load_config
    
    # Generate C2 keypair
    c2_pub, c2_priv = generate_key_pair()
    
    # Create configuration
    config_data = create_config(
        server_url="http://localhost:8080",
        deploy_id="test-deploy-001",
        callback_interval=5,
        c2_public_key=c2_pub
    )
    
    assert len(config_data) == 528, f"Config size wrong: {len(config_data)}"
    
    # Load and verify configuration
    agent_pub, agent_priv, config = load_config(config_data)
    
    assert config['server_url'] == "http://localhost:8080"
    assert config['deploy_id'] == "test-deploy-001"
    assert config['callback_interval'] == 5
    assert config['c2_public_key'] == c2_pub
    
    # Test crypto with loaded keys
    test_msg = b"Configuration test message"
    encrypted = encrypt(test_msg, c2_pub, agent_priv)
    decrypted = decrypt(encrypted, c2_priv, agent_pub)
    
    assert decrypted == test_msg, "Config crypto test failed"
    
    print("✓ Configuration crypto test passed")

def run_all_tests():
    """Run all crypto tests"""
    try:
        test_key_generation()
        test_encrypt_decrypt()
        test_decrypt_failure()
        test_configuration_crypto()
        print("\n✓ All crypto tests passed!")
        return True
    except Exception as e:
        print(f"\n✗ Crypto test failed: {e}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)