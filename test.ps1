# Run tests through docker-compose

function Show-Help {
    Write-Host "Usage: .\test.ps1 [options] [test-type] [name]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Help     Show this help message"
    Write-Host "  -Fast     Run without rebuilding containers"
    Write-Host ""
    Write-Host "Test types:"
    Write-Host "  group     Run a group of tests (unit, api, services, integration, performance)"
    Write-Host "  path      Run tests in a specific file"
    Write-Host "  test      Run a specific test by name"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\test.ps1                          # Run all tests"
    Write-Host "  .\test.ps1 -Fast group unit        # Run unit tests without rebuilding"
    Write-Host "  .\test.ps1 group api               # Run API tests"
    Write-Host "  .\test.ps1 path tests/models/test_user_model.py  # Run specific test file"
    Write-Host "  .\test.ps1 test test_create_user   # Run specific test"
}

param(
    [switch]$Help,
    [switch]$Fast,
    [string]$TestType,
    [string]$TestName
)

if ($Help) {
    Show-Help
    exit 0
}

$command = "python run_tests.py"

if ($TestType) {
    $command = "python run_tests.py $TestType $TestName"
}

if (-not $Fast) {
    docker-compose build backend
}

docker-compose run --rm backend $command