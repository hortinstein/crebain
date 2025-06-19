### Outline
This section of the repository defines various endpoint agents that serve a simple function.
1) They are configured with static data that defines encryption/calling address/id numbers that provide relevant metadata and this should be loaded as context. This is encrypted using a keypair that preprends the JSON.  This entire config should be stored in 128 bytes for keypair + max 400 bytes for JSON. This means an uncofigured binary should have 528 bytes that are reconfigured prior to execution or testing.  
2) They load this and decrypt. and execute a get request to the address that is in their configuration. It should include the deploy_id
3) The get request will be encoded by the server using the agent's public key. the agent will decrypt using it's private key, the task will be in JSON format: 
"""
{
    task_id: "server generated UUID",
    task_num: "0",
    task_arg: "command to be executed"
}
"""
4) it should execute the command in the command line and send a response encoded with the c2_public_key.  Response should be in the format
{
    task_id: "server generated UUID from original task",
    task_num: "0",
    task_arg: "command to be executed"
}
5) it should sleep and wait again for the sleep time.  

### Encryption
Monocypher should be used throughout the project (on all endpoints/agents and on the server testing). It should specifically use the ```crypto_lock``` and ```cypto_unlock``` functions. Here is an example in NIM: https://raw.githubusercontent.com/hortinstein/enkodo/refs/heads/master/src/enkodo.nim

### Testing

#### Unit tests
Unit tests should in the language the endpoint is implemented in and should include the following:
- check whether decrypt and encrypt functions can be used
- check decoding configuration works
- store static configurations as a sample in the file
- 

#### Integration tests
Integration tests should be able to be used across implementations.
1) It should configure a sample of the binary and run it for target endpoint
2) It should provide taskings that execute the following:
- echo "hello"

### Configuration Files:
Each agent should have 528 bytes of static configuration data that is stamped in.   

Testing Guidlines
- for each implementation unit testing should be done in it's own language
- integration testing should be done by the ```integration_tests``` folder which configures and starts each executable
- sample configurations are in ```integration_tests/agent_config.json``` and ```integration_tests/agent_config.json```
-  
Code Style Guidelines
- Python 3.9+ compatible code (for python code only)
- Type hints required for all functions and methods
- Do not use classes, use functions
- global state should not be used when it can be avoided
- Functions and variables should be short and concise
- Functions/Variables: snake_case
- Constants: UPPERCASE_WITH_UNDERSCORES
- Imports organization with isort:
  - Standard library imports
  - Third-party imports
  - Local application imports
- Error handling: Use specific exception types
- Logging: Use the logging module with appropriate levels, statements must not be present in debug mode

