#!/usr/bin/env python3
"""
Integration tests for Python endpoint agent.
Tests the complete agent functionality including configuration, encryption, and C2 communication.
"""

import json
import os
import subprocess
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Any, Optional
import unittest
import sys

# Add python directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from crypto_utils import generate_keypair, encrypt_message, decrypt_message, encode_key_b64
from config_manager import generate_sample_config


class MockC2Handler(BaseHTTPRequestHandler):
    """Mock C2 server for integration testing."""
    
    # Class variables to store test data
    tasks_queue = []
    responses_received = []
    c2_private_key = None
    c2_public_key = None
    agent_public_key = None
    
    def log_message(self, format: str, *args: Any) -> None:
        """Suppress HTTP server logging."""
        pass
    
    def do_GET(self) -> None:
        """Handle GET requests for task retrieval."""
        # Parse query parameters
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)
        
        deploy_id = params.get('deploy_id', [''])[0]
        
        if not deploy_id:
            self.send_response(400)
            self.end_headers()
            return
        
        # Check if there are tasks in the queue
        if self.tasks_queue:
            task = self.tasks_queue.pop(0)
            
            # Encrypt task for agent
            task_json = json.dumps(task)
            encrypted_task = encrypt_message(
                task_json,
                self.agent_public_key,
                self.c2_private_key
            )
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(encrypted_task.encode())
        else:
            # No tasks available
            self.send_response(204)
            self.end_headers()
    
    def do_POST(self) -> None:
        """Handle POST requests for response submission."""
        content_length = int(self.headers.get('Content-Length', 0))
        encrypted_response = self.rfile.read(content_length).decode()
        
        try:
            # Decrypt response from agent
            response_json = decrypt_message(
                encrypted_response,
                self.agent_public_key,
                self.c2_private_key
            )
            response_data = json.loads(response_json)
            
            # Store response for verification
            self.responses_received.append(response_data)
            
            self.send_response(200)
            self.end_headers()
            
        except Exception as e:
            print(f"Failed to decrypt response: {e}")
            self.send_response(500)
            self.end_headers()


class TestPythonEndpoint(unittest.TestCase):
    """Integration tests for Python endpoint agent."""
    
    def setUp(self) -> None:
        """Set up test environment."""
        # Generate keypairs
        self.c2_priv, self.c2_pub = generate_keypair()
        self.agent_priv, self.agent_pub = generate_keypair()
        
        # Set up mock C2 server
        MockC2Handler.c2_private_key = self.c2_priv
        MockC2Handler.c2_public_key = self.c2_pub
        MockC2Handler.agent_public_key = self.agent_pub
        MockC2Handler.tasks_queue = []
        MockC2Handler.responses_received = []
        
        # Start mock C2 server
        self.server = HTTPServer(('localhost', 0), MockC2Handler)
        self.server_port = self.server.server_address[1]
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Create agent configuration
        self.callback_url = f"http://localhost:{self.server_port}/callback"
        self.config_data = self.create_test_config()
        
        # Create temporary config file
        self.config_file = None
        
    def tearDown(self) -> None:
        """Clean up test environment."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        
        if self.config_file and os.path.exists(self.config_file):
            os.unlink(self.config_file)
    
    def create_test_config(self) -> bytes:
        """Create test configuration with custom settings."""
        config = {
            "build_id": "test_build_001",
            "deploy_id": "test_deploy_001",
            "kill_epoch": str(int(time.time()) + 3600),  # 1 hour from now
            "interval": "1000",  # 1 second for fast testing
            "callback": self.callback_url,
            "c2_pub_key": encode_key_b64(self.c2_pub),
            "agent_priv_key": encode_key_b64(self.agent_priv),
            "filler": ""
        }
        
        return generate_sample_config(self.c2_pub, self.agent_priv, self.agent_pub)
    
    def create_config_file(self) -> str:
        """Create temporary configuration file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(self.config_data)
            self.config_file = f.name
        return self.config_file
    
    def test_agent_startup_and_shutdown(self) -> None:
        """Test agent can start up and shut down properly."""
        config_file = self.create_config_file()
        
        # Start agent process
        agent_path = os.path.join(os.path.dirname(__file__), '..', 'python', 'agent.py')
        process = subprocess.Popen(
            [sys.executable, agent_path, config_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Let agent run for a short time
        time.sleep(2)
        
        # Terminate agent
        process.terminate()
        process.wait(timeout=5)
        
        # Check that process terminated cleanly
        self.assertIsNotNone(process.returncode)
    
    def test_agent_task_execution(self) -> None:
        """Test agent can receive and execute tasks."""
        config_file = self.create_config_file()
        
        # Add task to queue
        test_task = {
            "task_id": "test_task_001",
            "task_num": "0",
            "task_arg": "echo hello"
        }
        MockC2Handler.tasks_queue.append(test_task)
        
        # Start agent process
        agent_path = os.path.join(os.path.dirname(__file__), '..', 'python', 'agent.py')
        process = subprocess.Popen(
            [sys.executable, agent_path, config_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for task to be processed
        timeout = 10
        start_time = time.time()
        
        while len(MockC2Handler.responses_received) == 0 and time.time() - start_time < timeout:
            time.sleep(0.5)
        
        # Terminate agent
        process.terminate()
        process.wait(timeout=5)
        
        # Verify task was processed
        self.assertEqual(len(MockC2Handler.responses_received), 1)
        
        response = MockC2Handler.responses_received[0]
        self.assertEqual(response["task_id"], "test_task_001")
        self.assertEqual(response["task_num"], "0")
        self.assertEqual(response["task_result"], "hello")
    
    def test_agent_multiple_tasks(self) -> None:
        """Test agent can handle multiple tasks in sequence."""
        config_file = self.create_config_file()
        
        # Add multiple tasks to queue
        tasks = [
            {"task_id": "task_001", "task_num": "0", "task_arg": "echo task1"},
            {"task_id": "task_002", "task_num": "1", "task_arg": "echo task2"},
            {"task_id": "task_003", "task_num": "2", "task_arg": "echo task3"}
        ]
        
        for task in tasks:
            MockC2Handler.tasks_queue.append(task)
        
        # Start agent process
        agent_path = os.path.join(os.path.dirname(__file__), '..', 'python', 'agent.py')
        process = subprocess.Popen(
            [sys.executable, agent_path, config_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for all tasks to be processed
        timeout = 15
        start_time = time.time()
        
        while len(MockC2Handler.responses_received) < 3 and time.time() - start_time < timeout:
            time.sleep(0.5)
        
        # Terminate agent
        process.terminate()
        process.wait(timeout=5)
        
        # Verify all tasks were processed
        self.assertEqual(len(MockC2Handler.responses_received), 3)
        
        # Verify responses match tasks
        for i, response in enumerate(MockC2Handler.responses_received):
            expected_task = tasks[i]
            self.assertEqual(response["task_id"], expected_task["task_id"])
            self.assertEqual(response["task_num"], expected_task["task_num"])
            self.assertIn(f"task{i+1}", response["task_result"])
    
    def test_agent_error_handling(self) -> None:
        """Test agent handles command errors gracefully."""
        config_file = self.create_config_file()
        
        # Add task with invalid command
        test_task = {
            "task_id": "error_task_001",
            "task_num": "0",
            "task_arg": "invalidcommandthatdoesnotexist"
        }
        MockC2Handler.tasks_queue.append(test_task)
        
        # Start agent process
        agent_path = os.path.join(os.path.dirname(__file__), '..', 'python', 'agent.py')
        process = subprocess.Popen(
            [sys.executable, agent_path, config_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for task to be processed
        timeout = 10
        start_time = time.time()
        
        while len(MockC2Handler.responses_received) == 0 and time.time() - start_time < timeout:
            time.sleep(0.5)
        
        # Terminate agent
        process.terminate()
        process.wait(timeout=5)
        
        # Verify error was handled
        self.assertEqual(len(MockC2Handler.responses_received), 1)
        
        response = MockC2Handler.responses_received[0]
        self.assertEqual(response["task_id"], "error_task_001")
        self.assertEqual(response["task_num"], "0")
        self.assertIn("Return code:", response["task_result"])
    
    def test_config_file_validation(self) -> None:
        """Test configuration file validation."""
        # Test with invalid config size
        invalid_config = b"invalid_config_data"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(invalid_config)
            invalid_config_file = f.name
        
        try:
            agent_path = os.path.join(os.path.dirname(__file__), '..', 'python', 'agent.py')
            process = subprocess.Popen(
                [sys.executable, agent_path, invalid_config_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = process.communicate(timeout=5)
            
            # Should exit with error
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("528 bytes", stdout.decode() + stderr.decode())
            
        finally:
            os.unlink(invalid_config_file)


def run_integration_tests() -> None:
    """Run integration tests for Python endpoint."""
    print("Running Python endpoint integration tests...")
    
    # Check if Python agent files exist
    python_dir = os.path.join(os.path.dirname(__file__), '..', 'python')
    agent_file = os.path.join(python_dir, 'agent.py')
    
    if not os.path.exists(agent_file):
        print(f"Error: Python agent not found at {agent_file}")
        return False
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPythonEndpoint)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)