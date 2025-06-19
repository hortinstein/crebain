"""
Test server for agent communication
"""
import json
import uuid
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'python'))
from crypto import generate_key_pair, encrypt, decrypt

class C2Handler(BaseHTTPRequestHandler):
    """HTTP handler for C2 server"""
    
    def log_message(self, format, *args):
        """Override to reduce logging noise"""
        pass
    
    def do_POST(self):
        """Handle POST requests from agents"""
        content_length = int(self.headers.get('Content-Length', 0))
        encrypted_data = self.rfile.read(content_length)
        
        if self.path == '/beacon':
            self.handle_beacon(encrypted_data)
        elif self.path == '/result':
            self.handle_result(encrypted_data)
        else:
            self.send_error(404)
    
    def handle_beacon(self, encrypted_data: bytes):
        """Handle agent beacon and return task"""
        try:
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
            print(f"Received beacon from {beacon_info.get('deploy_id', 'unknown')}")
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
        """Handle task result from agent"""
        try:
            # Decrypt result data
            decrypted_data = decrypt(
                encrypted_data,
                self.server.c2_private_key,
                self.server.agent_public_key
            )
            
            if not decrypted_data:
                self.send_error(400, "Decryption failed")
                return
            
            result = json.loads(decrypted_data.decode('utf-8'))
            print(f"Received result for task {result.get('task_id', 'unknown')}")
            print(f"  Command: {result.get('task_arg', 'unknown')}")
            print(f"  Output: {result.get('output', 'no output')}")
            
            self.server.received_results.append(result)
            
            self.send_response(200)
            self.end_headers()
            
        except Exception as e:
            print(f"Result handling error: {e}")
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

def test_server_standalone():
    """Test server in standalone mode"""
    # Generate dummy agent key for testing
    dummy_agent_pub, _ = generate_key_pair()
    
    server = start_test_server(dummy_agent_pub, 8080)
    
    print("Test server running. Press Ctrl+C to stop.")
    print(f"C2 Public Key: {server.c2_public_key.hex()}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.shutdown()

if __name__ == "__main__":
    test_server_standalone()