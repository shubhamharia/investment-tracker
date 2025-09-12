#!/bin/bash
# Run tests through docker-compose

# Function to show help
show_help() {
    echo "Usage: ./test.sh [options] [test-type] [name]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -f, --fast     Run without rebuilding containers"
    echo ""
    echo "Test types:"
    echo "  group          Run a group of tests (unit, api, services, integration, performance)"
    echo "  path           Run tests in a specific file"
    echo "  test           Run a specific test by name"
    echo ""
    echo "Examples:"
    echo "  ./test.sh                          # Run all tests"
    echo "  ./test.sh -f group unit           # Run unit tests without rebuilding"
    echo "  ./test.sh group api               # Run API tests"
    echo "  ./test.sh path tests/models/test_user_model.py  # Run specific test file"
    echo "  ./test.sh test test_create_user   # Run specific test"
}

# Default values
REBUILD=true
COMMAND="python run_tests.py"

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -f|--fast)
            REBUILD=false
            shift
            ;;
        group|path|test)
            COMMAND="python run_tests.py $1 $2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Build and run tests
if [ "$REBUILD" = true ]; then
    docker-compose build backend
fi

docker-compose run --rm backend $COMMAND