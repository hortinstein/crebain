"""
Integration test for Python agent
"""
import os
import sys
import time
import subprocess
import threading
from test_server import start_test_server
from test_configure import create_configured_agent

def test_python_agent():
    """Test complete Python agent functionality"""
    print("Starting Python agent integration test...")
    
    # Create configured agent
    agent_path, c2_public_key = create_configured_agent(
        server_url="http://localhost:8080",
        deploy_id="integration-test-001",
        callback_interval=2,
        output_dir="./bin"
    )
    
    config_path = os.path.join("./bin", "config_integration-test-001.bin")
    
    # Extract agent public key from config for server
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'python'))
    from configure import load_config
    
    with open(config_path, 'rb') as f:
        config_data = f.read()
    
    agent_public_key, _, _ = load_config(config_data)
    
    # Start test server
    server = start_test_server(agent_public_key, 8080)
    
    print(f"Server started with C2 public key: {server.c2_public_key.hex()}")
    
    # Update config with correct C2 public key
    from configure import create_config
    updated_config = create_config(
        server_url="http://localhost:8080",
        deploy_id="integration-test-001", 
        callback_interval=2,
        c2_public_key=server.c2_public_key
    )
    
    with open(config_path, 'wb') as f:
        f.write(updated_config)
    
    print("Starting agent...")
    
    # Start agent process
    agent_process = subprocess.Popen([
        sys.executable, agent_path, config_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait for agent to communicate
    test_duration = 15  # seconds
    start_time = time.time()
    
    print(f"Running test for {test_duration} seconds...")
    
    while time.time() - start_time < test_duration:
        if len(server.received_results) > 0:
            break
        time.sleep(0.5)
    
    # Terminate agent
    agent_process.terminate()
    try:
        stdout, stderr = agent_process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        agent_process.kill()
        stdout, stderr = agent_process.communicate()
    
    # Stop server
    server.shutdown()
    
    # Check results
    success = len(server.received_results) > 0
    
    print(f"\nTest Results:")
    print(f"Agent output: {stdout}")
    if stderr:
        print(f"Agent errors: {stderr}")
    
    print(f"Server received {len(server.received_results)} results")
    
    if success:
        result = server.received_results[0]
        print(f"First result:")
        print(f"  Task ID: {result.get('task_id')}")
        print(f"  Command: {result.get('task_arg')}")
        print(f"  Output: {result.get('output', '').strip()}")
        
        # Verify echo command worked
        if 'hello' in result.get('output', '').lower():
            print("✓ Command execution successful!")
        else:
            print("✗ Command execution failed!")
            success = False
    
    return success

def run_comprehensive_test():
    """Run all integration tests"""
    print("Running comprehensive Python agent tests...")
    print("=" * 50)
    
    # Test crypto functions
    print("\n1. Testing crypto functions...")
    from test_crypto import run_all_tests
    crypto_success = run_all_tests()
    
    # Test configuration
    print("\n2. Testing configuration...")
    from test_configure import test_configuration_loading
    try:
        test_configuration_loading()
        config_success = True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        config_success = False
    
    # Test full agent
    print("\n3. Testing full agent functionality...")
    agent_success = test_python_agent()
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"Crypto tests: {'✓ PASS' if crypto_success else '✗ FAIL'}")
    print(f"Config tests: {'✓ PASS' if config_success else '✗ FAIL'}")
    print(f"Agent tests: {'✓ PASS' if agent_success else '✗ FAIL'}")
    
    overall_success = crypto_success and config_success and agent_success
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if overall_success else '✗ SOME TESTS FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)