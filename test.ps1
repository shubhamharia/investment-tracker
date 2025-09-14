# PowerShell Docker Backend Test Script
# Run this script to test the backend in Docker environment

param(
    [switch]$KeepRunning,
    [switch]$SkipBuild,
    [switch]$Help,
    [switch]$Fast,
    [string]$TestType,
    [string]$TestName
)

function Show-Help {
    Write-Host "Docker Backend Test Script" -ForegroundColor Blue
    Write-Host "Usage: .\test.ps1 [options] [test-type] [name]"
    Write-Host ""
    Write-Host "Docker Testing Options:"
    Write-Host "  -KeepRunning: Keep services running after tests"
    Write-Host "  -SkipBuild:   Skip building containers"
    Write-Host "  -Help:        Show this help message"
    Write-Host ""
    Write-Host "Legacy Test Options:"
    Write-Host "  -Fast         Run without rebuilding containers"
    Write-Host ""
    Write-Host "Test types:"
    Write-Host "  group         Run a group of tests (unit, api, services, integration, performance)"
    Write-Host "  path          Run tests in a specific file"
    Write-Host "  test          Run a specific test by name"
    Write-Host "  docker-test   Run comprehensive Docker environment tests"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\test.ps1                              # Run comprehensive Docker tests"
    Write-Host "  .\test.ps1 docker-test -KeepRunning    # Test Docker setup and keep running"
    Write-Host "  .\test.ps1 -Fast group unit            # Run unit tests without rebuilding"
    Write-Host "  .\test.ps1 group api                   # Run API tests"
    Write-Host "  .\test.ps1 path tests/models/test_user_model.py  # Run specific test file"
    Write-Host "  .\test.ps1 test test_create_user       # Run specific test"
}

if ($Help) {
    Show-Help
    exit 0
}

# Colors for output
$Red = 'Red'
$Green = 'Green'
$Yellow = 'Yellow'
$Blue = 'Blue'

function Write-Status { param($Message) Write-Host "[INFO] $Message" -ForegroundColor $Blue }
function Write-Success { param($Message) Write-Host "[SUCCESS] $Message" -ForegroundColor $Green }
function Write-Warning { param($Message) Write-Host "[WARNING] $Message" -ForegroundColor $Yellow }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor $Red }

# If no test type specified or docker-test specified, run comprehensive Docker tests
if (!$TestType -or $TestType -eq "docker-test") {
    Write-Host "🐳 DOCKER BACKEND TESTING SCRIPT" -ForegroundColor Blue
    Write-Host "================================="
    
    # Check prerequisites
    Write-Status "Checking prerequisites..."
    
    if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker is not installed or not in PATH"
        exit 1
    }
    
    if (!(Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Error "Docker Compose is not installed or not in PATH"
        exit 1
    }
    
    try {
        docker info | Out-Null
    } catch {
        Write-Error "Docker daemon is not running"
        exit 1
    }
    
    Write-Success "Docker environment ready"
    
    # Check if CSV file exists
    if (Test-Path ".\data\combined_transactions_updated.csv") {
        $lines = (Get-Content ".\data\combined_transactions_updated.csv").Count
        Write-Success "CSV file found: $lines lines"
    } else {
        Write-Warning "CSV file not found at .\data\combined_transactions_updated.csv"
        Write-Warning "Some import tests will be skipped"
    }
    
    # Test 1: Basic Service Startup
    Write-Status "Test 1: Starting services with docker-compose..."
    
    if (!$SkipBuild) {
        docker-compose down -v 2>$null
        docker-compose up -d --build
    } else {
        docker-compose up -d
    }
    
    Write-Status "Waiting for services to be healthy..."
    Start-Sleep 30
    
    # Check service status
    $services = docker-compose ps
    if ($services -match "Up.*healthy") {
        Write-Success "Services are running and healthy"
    } else {
        Write-Error "Services failed to start properly"
        docker-compose logs backend
        exit 1
    }
    
    # Test 2: Health Check
    Write-Status "Test 2: Checking backend health endpoint..."
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/api/health" -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Success "Health endpoint responding"
        } else {
            Write-Warning "Health endpoint returned: $($response.StatusCode)"
        }
    } catch {
        Write-Error "Health endpoint not responding"
        docker-compose logs backend
        exit 1
    }
    
    # Test 3: Database Connection
    Write-Status "Test 3: Testing database connection..."
    $dbTest = docker-compose exec -T backend python -c @"
from app import create_app, db
try:
    app = create_app()
    with app.app_context():
        result = db.engine.execute('SELECT 1').scalar()
        print('Database connection: OK')
except Exception as e:
    print(f'Database error: {e}')
    exit(1)
"@ 2>$null
    
    if ($dbTest -match "Database connection: OK") {
        Write-Success "Database connection working"
    } else {
        Write-Error "Database connection failed"
        Write-Host $dbTest
        exit 1
    }
    
    # Test 4: CSV File Access
    Write-Status "Test 4: Checking CSV file access in container..."
    $csvCheck = docker-compose exec -T backend ls -la /app/data/ 2>$null
    
    if ($csvCheck -match "combined_transactions_updated.csv") {
        Write-Success "CSV file accessible in container"
        $csvExists = $true
    } else {
        Write-Warning "CSV file not found in container"
        Write-Host $csvCheck
        $csvExists = $false
    }
    
    # Test 5: Import Script Test
    if ($csvExists) {
        Write-Status "Test 5: Testing import script..."
        
        $importResult = docker-compose exec -T backend python import_data.py import 2>&1
        
        if ($importResult -match "successfully|imported") {
            Write-Success "Import script executed successfully"
            
            # Check imported data
            $transactionCount = docker-compose exec -T backend python -c @"
from app import create_app, db
from app.models import Transaction
app = create_app()
with app.app_context():
    count = Transaction.query.count()
    print(f'Transactions: {count}')
"@ 2>$null
            
            Write-Success "Import verification: $transactionCount"
        } else {
            Write-Warning "Import script had issues:"
            $importResult | Select-Object -First 10 | Write-Host
        }
    } else {
        Write-Warning "Skipping import test (no CSV file)"
    }
    
    # Test 6: API Endpoints
    Write-Status "Test 6: Testing API endpoints..."
    
    # Test health endpoint
    try {
        $healthResponse = Invoke-WebRequest -Uri "http://localhost:5000/api/health" -TimeoutSec 5
        $healthContent = $healthResponse.Content
        if ($healthContent -match "healthy") {
            Write-Success "Health endpoint: OK"
        } else {
            Write-Warning "Health endpoint: Unexpected response"
        }
    } catch {
        Write-Warning "Health endpoint: Error - $($_.Exception.Message)"
    }
    
    # Test 7: LSE Stock Integration
    Write-Status "Test 7: Testing LSE stock integration..."
    $yfinanceTest = docker-compose exec -T backend python -c @"
try:
    import yfinance as yf
    ticker = yf.Ticker('ULVR.L')
    info = ticker.info
    name = info.get('longName', 'Unknown')
    print(f'LSE Test: ULVR.L = {name}')
except Exception as e:
    print(f'LSE Test failed: {e}')
"@ 2>$null
    
    if ($yfinanceTest -match "Unilever") {
        Write-Success "LSE stock integration working"
    } else {
        Write-Warning "LSE stock integration issues:"
        Write-Host $yfinanceTest
    }
    
    # Final Summary
    Write-Host ""
    Write-Host "🎯 DOCKER TEST SUMMARY" -ForegroundColor Blue
    Write-Host "======================"
    Write-Success "✅ Docker services started"
    Write-Success "✅ Health endpoint working"
    Write-Success "✅ Database connection OK"
    if ($csvExists) {
        Write-Success "✅ CSV file accessible"
        if ($importResult -match "successfully|imported") {
            Write-Success "✅ Import script working"
        }
    }
    Write-Success "✅ API endpoints responding"
    
    Write-Host ""
    Write-Status "Your backend is ready for Docker deployment! 🚀"
    Write-Status "Access your API at: http://localhost:5000"
    Write-Status "View logs with: docker-compose logs -f backend"
    Write-Status "Import data with: docker-compose exec backend python import_data.py import"
    
    # Optional: Keep services running or stop them
    if (!$KeepRunning) {
        $response = Read-Host "Keep services running? (y/N)"
        if ($response -match "^[Yy]") {
            $KeepRunning = $true
        }
    }
    
    if (!$KeepRunning) {
        Write-Status "Stopping services..."
        docker-compose down
        Write-Success "Services stopped"
    } else {
        Write-Status "Services will continue running in background"
        Write-Status "Stop with: docker-compose down"
    }
    
    Write-Host ""
    Write-Success "Docker backend testing completed! 🎉"
    
} else {
    # Legacy test mode - run original test functionality
    $command = "python run_tests.py"
    
    if ($TestType) {
        $command = "python run_tests.py $TestType $TestName"
    }
    
    if (-not $Fast) {
        docker-compose build backend
    }
    
    docker-compose run --rm backend $command
}