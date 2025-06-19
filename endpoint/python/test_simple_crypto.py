#!/usr/bin/env python3
"""
Test the simplified crypto implementation to verify it works correctly.
"""

from crypto_utils import generate_keypair, encrypt_message, decrypt_message, encode_key_b64, decode_key_b64
import json

def test_basic_crypto():
    """Test basic crypto operations."""
    print("Testing basic crypto operations...")
    
    # Generate keypairs for Alice and Bob
    alice_priv, alice_pub = generate_keypair()
    bob_priv, bob_pub = generate_keypair()
    
    print(f"Alice public key: {encode_key_b64(alice_pub)[:20]}...")
    print(f"Bob public key: {encode_key_b64(bob_pub)[:20]}...")
    
    # Test simple message
    message = "Hello World"
    print(f"\nOriginal message: '{message}'")
    
    # Alice sends to Bob
    encrypted = encrypt_message(message, bob_pub, alice_priv)
    print(f"Encrypted message: {encrypted}")
    
    # Bob receives from Alice
    decrypted = decrypt_message(encrypted, alice_pub, bob_priv)
    print(f"Decrypted message: '{decrypted}'")
    
    success = (message == decrypted)
    print(f"✅ Basic test: {'PASSED' if success else 'FAILED'}")
    
    if not success:
        return False
    
    # Test JSON message (agent task format)
    task = {
        "task_id": "test_task_001",
        "task_num": "0",
        "task_arg": "echo hello"
    }
    task_json = json.dumps(task)
    print(f"\nTesting JSON message: {task_json}")
    
    encrypted_json = encrypt_message(task_json, bob_pub, alice_priv)
    decrypted_json = decrypt_message(encrypted_json, alice_pub, bob_priv)
    
    json_success = (task_json == decrypted_json)
    print(f"✅ JSON test: {'PASSED' if json_success else 'FAILED'}")
    
    if json_success:
        parsed_task = json.loads(decrypted_json)
        print(f"Task ID: {parsed_task['task_id']}")
        print(f"Task arg: {parsed_task['task_arg']}")
    
    return success and json_success

def test_reverse_communication():
    """Test Bob to Alice communication."""
    print("\nTesting reverse communication (Bob -> Alice)...")
    
    alice_priv, alice_pub = generate_keypair()
    bob_priv, bob_pub = generate_keypair()
    
    # Response from Bob to Alice
    response = {
        "task_id": "test_task_001",
        "task_num": "0",
        "task_result": "hello"
    }
    response_json = json.dumps(response)
    
    print(f"Bob's response: {response_json}")
    
    # Bob sends to Alice
    encrypted_response = encrypt_message(response_json, alice_pub, bob_priv)
    print(f"Encrypted response: {encrypted_response[:50]}...")
    
    # Alice receives from Bob
    decrypted_response = decrypt_message(encrypted_response, bob_pub, alice_priv)
    print(f"Decrypted response: {decrypted_response}")
    
    success = (response_json == decrypted_response)
    print(f"✅ Reverse test: {'PASSED' if success else 'FAILED'}")
    
    return success

if __name__ == "__main__":
    print("Simple Crypto Test Suite")
    print("=" * 40)
    
    test1 = test_basic_crypto()
    test2 = test_reverse_communication()
    
    print("\n" + "=" * 40)
    if test1 and test2:
        print("🎉 All crypto tests PASSED!")
    else:
        print("💥 Some crypto tests FAILED!")
        print("Note: This is a simplified demonstration implementation.")
        print("In production, use proper Monocypher or similar crypto libraries.")