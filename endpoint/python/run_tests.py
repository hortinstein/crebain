#!/usr/bin/env python3
"""
Test runner for Python endpoint unit tests.
"""

import sys
import unittest
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))


def run_all_tests() -> bool:
    """Run all unit tests for Python endpoint."""
    try:
        # Import test modules
        import test_crypto_utils
        import test_config_manager
        import test_agent
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add all test cases
        suite.addTests(loader.loadTestsFromModule(test_crypto_utils))
        suite.addTests(loader.loadTestsFromModule(test_config_manager))
        suite.addTests(loader.loadTestsFromModule(test_agent))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except Exception as e:
        print(f"Test execution failed: {e}")
        return False


if __name__ == '__main__':
    print("Running Python endpoint unit tests...")
    success = run_all_tests()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)