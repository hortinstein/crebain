# Endpoint Agents

This directory contains endpoint agent implementations for the Ungoliant C2 platform.

## Overview

Endpoint agents are lightweight binaries that:
1. Load embedded 528-byte configuration containing encryption keys and C2 details
2. Communicate with C2 server using encrypted channels
3. Execute commands and return encrypted results
4. Operate on configurable intervals with kill-date functionality

## Architecture

### Configuration Format
- **Total Size**: 528 bytes
- **Keypair Section**: 128 bytes (64-byte public key + 64-byte private key)
- **JSON Config**: 400 bytes containing:
  - `build_id`: Build identifier
  - `deploy_id`: Deployment identifier  
  - `kill_epoch`: Unix timestamp for automatic termination
  - `interval`: Callback interval in milliseconds
  - `callback`: C2 server URL
  - `c2_pub_key`: C2 server public key (base64)
  - `agent_priv_key`: Agent private key (base64)
  - `filler`: Padding to exact 400 bytes

### Communication Protocol
1. **Task Request**: Agent makes GET request to C2 with `deploy_id` parameter
2. **Task Response**: C2 returns encrypted task JSON or 204 (no tasks)
3. **Task Execution**: Agent decrypts, executes command, captures output
4. **Result Submission**: Agent encrypts result and POSTs back to C2

### Task Format
```json
{
    "task_id": "server_generated_uuid",
    "task_num": "sequence_number", 
    "task_arg": "command_to_execute"
}
```

### Response Format
```json
{
    "task_id": "original_task_id",
    "task_num": "original_task_num",
    "task_result": "command_output"
}
```

## Python Implementation

### Files
- `agent.py` - Main agent executable
- `crypto_utils.py` - Monocypher-compatible encryption
- `config_manager.py` - 528-byte configuration handling
- `requirements.txt` - Python dependencies

### Dependencies
- `requests` - HTTP communication
- `pycryptodome` - Cryptographic operations (X25519 + ChaCha20-Poly1305)

### Usage
```bash
# Install dependencies
pip install -r python/requirements.txt

# Run agent with configuration file
python python/agent.py config.bin
```

## Testing

### Unit Tests
Located in `python/` directory:
- `test_crypto_utils.py` - Encryption/decryption tests
- `test_config_manager.py` - Configuration packing/unpacking tests  
- `test_agent.py` - Agent functionality tests

Run unit tests:
```bash
cd python
python run_tests.py
```

### Integration Tests  
Located in `integration_tests/` directory:
- `test_python_endpoint.py` - End-to-end agent testing with mock C2
- `run_all_tests.py` - Complete test suite runner

Run integration tests:
```bash
cd integration_tests
python run_all_tests.py
```

The integration tests:
- Generate sample configurations
- Start mock C2 server
- Test agent startup/shutdown
- Verify task execution (including `echo "hello"`)
- Test error handling
- Validate encryption/decryption

## Configuration Generation

Use the integration test framework to generate valid configurations:

```bash
cd integration_tests
python run_all_tests.py  # Generates agent_config.bin and server_config.json
```

## Security Features

- **End-to-End Encryption**: All C2 communication encrypted with X25519 + ChaCha20-Poly1305
- **Key Isolation**: Each agent has unique keypair
- **Kill Date**: Automatic termination after specified epoch
- **Command Sandboxing**: Commands executed in subprocess with timeout

## Development Guidelines

- Python 3.9+ compatibility
- Type hints required
- Function-based architecture (no classes)
- Comprehensive error handling
- Structured logging
- 30-second command timeout
- No debug logging in production