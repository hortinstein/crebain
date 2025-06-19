"""
Agent configuration script for integration testing
"""
import os
import sys
import shutil
from typing import Optional

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'python'))
from configure import create_config
from crypto import generate_key_pair

def create_configured_agent(
    server_url: str = "http://localhost:8080",
    deploy_id: str = "test-agent-001", 
    callback_interval: int = 5,
    c2_public_key: Optional[bytes] = None,
    output_dir: str = "./bin"
) -> tuple[str, bytes]:
    """Create a configured Python agent"""
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate C2 keypair if not provided
    if c2_public_key is None:
        c2_public_key, c2_private_key = generate_key_pair()
        print(f"Generated C2 public key: {c2_public_key.hex()}")
        print(f"Generated C2 private key: {c2_private_key.hex()}")
    
    # Create configuration
    config_data = create_config(
        server_url=server_url,
        deploy_id=deploy_id,
        callback_interval=callback_interval,
        c2_public_key=c2_public_key
    )
    
    # Copy agent.py to output directory as configured agent
    agent_source = os.path.join(os.path.dirname(__file__), '..', 'python', 'agent.py')
    configured_agent_path = os.path.join(output_dir, f"configured_agent_{deploy_id}.py")
    
    shutil.copy2(agent_source, configured_agent_path)
    
    # Copy supporting modules
    python_dir = os.path.join(os.path.dirname(__file__), '..', 'python')
    modules_to_copy = ['configure.py', 'crypto.py']
    
    for module in modules_to_copy:
        module_source = os.path.join(python_dir, module)
        module_dest = os.path.join(output_dir, module)
        shutil.copy2(module_source, module_dest)
    
    # Create a configuration file for the agent
    config_path = os.path.join(output_dir, f"config_{deploy_id}.bin")
    with open(config_path, 'wb') as f:
        f.write(config_data)
    
    print(f"Created configured agent: {configured_agent_path}")
    print(f"Created configuration: {config_path}")
    print(f"Deploy ID: {deploy_id}")
    print(f"Server URL: {server_url}")
    print(f"Callback interval: {callback_interval}s")
    
    return configured_agent_path, c2_public_key

def create_sample_configurations():
    """Create sample configurations for testing"""
    print("Creating sample agent configurations...")
    
    # Create multiple test agents
    configs = [
        {
            "deploy_id": "python-test-001",
            "server_url": "http://localhost:8080",
            "callback_interval": 5
        },
        {
            "deploy_id": "python-test-002", 
            "server_url": "http://localhost:8081",
            "callback_interval": 10
        }
    ]
    
    agent_paths = []
    c2_keys = []
    
    for config in configs:
        agent_path, c2_key = create_configured_agent(**config)
        agent_paths.append(agent_path)
        c2_keys.append(c2_key)
    
    return agent_paths, c2_keys

def test_configuration_loading():
    """Test that configurations can be loaded properly"""
    from configure import load_config
    
    print("Testing configuration loading...")
    
    # Create a test configuration
    c2_pub, c2_priv = generate_key_pair()
    config_data = create_config(
        server_url="http://test.example.com:9999",
        deploy_id="load-test-123",
        callback_interval=30,
        c2_public_key=c2_pub
    )
    
    # Load and verify
    agent_pub, agent_priv, config = load_config(config_data)
    
    assert config['server_url'] == "http://test.example.com:9999"
    assert config['deploy_id'] == "load-test-123"
    assert config['callback_interval'] == 30
    assert config['c2_public_key'] == c2_pub
    assert len(agent_pub) == 32
    assert len(agent_priv) == 32
    
    print("✓ Configuration loading test passed")

def main():
    """Main configuration script"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_configuration_loading()
            return
        elif sys.argv[1] == "samples":
            create_sample_configurations()
            return
    
    # Interactive configuration
    print("Agent Configuration Tool")
    print("========================")
    
    server_url = input("Server URL [http://localhost:8080]: ").strip()
    if not server_url:
        server_url = "http://localhost:8080"
    
    deploy_id = input("Deploy ID [python-agent-001]: ").strip()
    if not deploy_id:
        deploy_id = "python-agent-001"
    
    callback_str = input("Callback interval in seconds [5]: ").strip()
    callback_interval = int(callback_str) if callback_str else 5
    
    agent_path, c2_key = create_configured_agent(
        server_url=server_url,
        deploy_id=deploy_id,
        callback_interval=callback_interval
    )
    
    print(f"\nAgent configured successfully!")
    print(f"To run: python {agent_path} bin/config_{deploy_id}.bin")

if __name__ == "__main__":
    main()