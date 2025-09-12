#!/usr/bin/env python
import sys
import subprocess

TEST_GROUPS = {
    'unit': [
        'tests/models/test_user_model.py',
        'tests/models/test_portfolio_model.py',
        'tests/models/test_holding_model.py',
        'tests/models/test_dividend_model.py',
        'tests/models/test_price_history_model.py',
    ],
    'api': [
        'tests/api/test_users.py',
        'tests/api/test_holdings_api.py',
        'tests/api/test_portfolio_api.py',
        'tests/api/test_securities_api.py',
    ],
    'services': [
        'tests/services/test_dividend_service.py',
        'tests/services/test_price_service.py',
    ],
    'integration': [
        'tests/integration/test_celery_tasks.py',
        'tests/integration/test_data_consistency.py',
        'tests/integration/test_portfolio_operations.py',
        'tests/integration/test_transaction_flow.py',
    ],
    'performance': [
        'tests/performance/test_performance.py',
    ],
}

def run_tests(test_group=None, test_path=None, test_name=None):
    """Run tests based on provided parameters."""
    base_command = ['pytest', '-v']
    
    if test_name:
        # Run specific test
        base_command.extend(['-k', test_name])
        if test_path:
            base_command.append(test_path)
    elif test_group:
        # Run test group
        if test_group in TEST_GROUPS:
            base_command.extend(TEST_GROUPS[test_group])
        else:
            print(f"Unknown test group: {test_group}")
            print("Available groups:", list(TEST_GROUPS.keys()))
            return 1
    elif test_path:
        # Run specific test file
        base_command.append(test_path)
    else:
        # Run all tests
        base_command.append('tests/')
    
    result = subprocess.run(base_command)
    return result.returncode

def print_help():
    """Print usage instructions."""
    print("Usage:")
    print("  ./run_tests.py [group|path|test] [name]")
    print("\nExamples:")
    print("  ./run_tests.py                    # Run all tests")
    print("  ./run_tests.py group unit         # Run unit tests")
    print("  ./run_tests.py group api          # Run API tests")
    print("  ./run_tests.py path tests/models/test_user_model.py  # Run specific test file")
    print("  ./run_tests.py test test_create_user                 # Run specific test")
    print("\nAvailable groups:")
    for group in TEST_GROUPS:
        print(f"  - {group}")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        # No arguments - run all tests
        sys.exit(run_tests())
    elif sys.argv[1] == 'help':
        print_help()
        sys.exit(0)
    elif len(sys.argv) >= 3:
        if sys.argv[1] == 'group':
            sys.exit(run_tests(test_group=sys.argv[2]))
        elif sys.argv[1] == 'path':
            sys.exit(run_tests(test_path=sys.argv[2]))
        elif sys.argv[1] == 'test':
            sys.exit(run_tests(test_name=sys.argv[2]))
    else:
        print_help()
        sys.exit(1)