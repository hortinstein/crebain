#!/usr/bin/env python3
"""
Main test runner for Python agent integration tests
"""
import sys
import os

def main():
    """Run integration tests based on command line argument"""
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py <test_type>")
        print("Available tests:")
        print("  crypto     - Test encryption/decryption functions")
        print("  config     - Test agent configuration")
        print("  server     - Start test server")
        print("  agent      - Test full agent functionality")
        print("  all        - Run all tests")
        sys.exit(1)
    
    test_type = sys.argv[1].lower()
    
    if test_type == "crypto":
        from test_crypto import run_all_tests
        success = run_all_tests()
    elif test_type == "config":
        from test_configure import test_configuration_loading
        try:
            test_configuration_loading()
            success = True
        except Exception as e:
            print(f"Configuration test failed: {e}")
            success = False
    elif test_type == "server":
        from test_server import test_server_standalone
        test_server_standalone()
        return
    elif test_type == "agent":
        from test_python import test_python_agent
        success = test_python_agent()
    elif test_type == "all":
        from test_python import run_comprehensive_test
        success = run_comprehensive_test()
    else:
        print(f"Unknown test type: {test_type}")
        sys.exit(1)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()