# Docker Backend Testing Guide

This guide will help you test the Investment Tracker backend in a Docker environment, including the import functionality with your CSV data.

## 📋 Prerequisites

- Docker Desktop installed and running
- Docker Compose v2 or higher
- Your CSV file in the `data/` directory
- Basic knowledge of Docker commands

## 🏗️ Docker Environment Setup

### 1. Project Structure
```
investment-tracker/
├── backend/
│   ├── import_data.py          ← CSV import script
│   ├── Dockerfile              ← Backend container config
│   ├── docker-entrypoint.sh    ← Container startup script
│   ├── requirements.txt        ← Python dependencies
│   └── app/                    ← Flask application
├── data/
│   └── combined_transactions_updated.csv  ← Your transaction data
├── docker-compose.yml          ← Multi-service orchestration
└── docker-compose.test.yml     ← Testing configuration
```

## 🐳 Testing Methods

### Method 1: Quick Backend Test (Recommended for Development)

**Step 1: Build and Start Services**
```bash
# Navigate to project root
cd investment-tracker

# Build and start all services
docker-compose up --build -d

# Check service status
docker-compose ps
```

**Step 2: Verify Backend Health**
```bash
# Check backend health endpoint
curl http://localhost:5000/api/health

# Expected response:
# {"status": "healthy", "timestamp": "2025-09-14T12:00:00"}
```

**Step 3: Test Database Connection**
```bash
# Connect to backend container
docker-compose exec backend bash

# Inside container - test database
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    print('Database connection:', db.engine.url)
    print('Tables:', db.engine.table_names())
"
```

### Method 2: CSV Import Testing

**Step 1: Verify CSV File Mount**
```bash
# Check if CSV file is accessible in container
docker-compose exec backend ls -la /app/data/

# Expected output:
# -rw-r--r-- 1 root root 28198 Sep 14 12:00 combined_transactions_updated.csv
```

**Step 2: Test Import Script**
```bash
# Run import script inside container
docker-compose exec backend python import_data.py import

# Expected output:
# CSV file found: /app/data/combined_transactions_updated.csv
# Processing 337 transactions...
# Imported 337 transactions successfully
```

**Step 3: Verify Data Import**
```bash
# Check imported data
docker-compose exec backend python -c "
from app import create_app, db
from app.models import Transaction, Security, Platform
app = create_app()
with app.app_context():
    print(f'Transactions: {Transaction.query.count()}')
    print(f'Securities: {Security.query.count()}')
    print(f'Platforms: {Platform.query.count()}')
"
```

### Method 3: Comprehensive API Testing

**Step 1: Test Authentication**
```bash
# Create test user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
  }'

# Login and get token
TOKEN=$(curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"
```

**Step 2: Test Portfolio Endpoints**
```bash
# Get portfolios (should be empty initially)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/portfolios

# Create a test portfolio
curl -X POST http://localhost:5000/api/portfolios \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Portfolio",
    "description": "Docker test portfolio"
  }'
```

**Step 3: Test Data Endpoints**
```bash
# Get securities (should show imported stocks)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/securities

# Get platforms (should show Trading212, etc.)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/platforms
```

## 🧪 Testing Scenarios

### Scenario 1: Fresh Database Import
```bash
# Clean slate test
docker-compose down -v  # Remove volumes
docker-compose up -d
docker-compose exec backend python import_data.py import
```

### Scenario 2: LSE Stock Price Testing
```bash
# Test yfinance integration for LSE stocks
docker-compose exec backend python -c "
import yfinance as yf
stocks = ['ULVR.L', 'HSBA.L', 'SHEL.L']
for stock in stocks:
    ticker = yf.Ticker(stock)
    info = ticker.info
    print(f'{stock}: {info.get(\"longName\", \"Unknown\")}')
"
```

### Scenario 3: Performance Testing
```bash
# Load test with ab (Apache Bench)
docker run --rm --network investment-tracker_portfolio_network \
  httpd:alpine ab -n 100 -c 10 http://backend:5000/api/health
```

## 📊 Monitoring and Logs

### View Service Logs
```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Database only
docker-compose logs -f db

# Last 50 lines
docker-compose logs --tail 50 backend
```

### Monitor Resource Usage
```bash
# Container stats
docker stats

# Service-specific stats
docker-compose top backend
```

## 🔧 Troubleshooting

### Common Issues and Solutions

**Issue 1: Database Connection Failed**
```bash
# Check database is running
docker-compose ps db

# Verify database health
docker-compose exec db pg_isready -U postgres

# Check network connectivity
docker-compose exec backend nc -zv db 5432
```

**Issue 2: CSV File Not Found**
```bash
# Verify volume mount
docker-compose exec backend ls -la /app/data/

# Check docker-compose.yml volumes section
# Should have: - ./data:/app/data
```

**Issue 3: Import Script Errors**
```bash
# Check Python path
docker-compose exec backend python -c "import sys; print(sys.path)"

# Test import_data module
docker-compose exec backend python -c "from import_data import get_default_csv_path; print(get_default_csv_path())"
```

**Issue 4: yfinance/LSE Stock Issues**
```bash
# Test yfinance installation
docker-compose exec backend pip list | grep yfinance

# Test simple yfinance call
docker-compose exec backend python -c "import yfinance as yf; print(yf.Ticker('AAPL').info.get('longName'))"
```

## 🧪 Automated Testing Suite

### Run Unit Tests in Docker
```bash
# Run all backend tests
docker-compose exec backend python -m pytest tests/ -v

# Run specific test categories
docker-compose exec backend python -m pytest tests/unit/ -v
docker-compose exec backend python -m pytest tests/integration/ -v

# Run with coverage
docker-compose exec backend python -m pytest tests/ --cov=app --cov-report=html
```

### Run Import-Specific Tests
```bash
# Test import functionality
docker-compose exec backend python -m pytest tests/test_import_data.py -v

# Test LSE compatibility
docker-compose exec backend python -m pytest tests/test_lse_compatibility.py -v

# Test relative paths
docker-compose exec backend python tests/test_relative_paths.py
```

## 🚀 Production Simulation

### Test with Production-like Settings
```bash
# Use production docker-compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Test with environment variables
FLASK_ENV=production docker-compose up -d
```

### Test Data Persistence
```bash
# Import data
docker-compose exec backend python import_data.py import

# Stop and restart services
docker-compose down
docker-compose up -d

# Verify data persisted
docker-compose exec backend python -c "
from app import create_app, db
from app.models import Transaction
app = create_app()
with app.app_context():
    print(f'Transactions after restart: {Transaction.query.count()}')
"
```

## 📝 Test Checklist

### ✅ Backend Functionality
- [ ] Container builds successfully
- [ ] Database connection established
- [ ] Health endpoint responds
- [ ] Authentication works
- [ ] API endpoints accessible

### ✅ Import Functionality  
- [ ] CSV file accessible in container
- [ ] import_data.py executes without errors
- [ ] Transactions imported successfully
- [ ] LSE stocks work with yfinance
- [ ] Fee calculations correct

### ✅ Data Persistence
- [ ] Data survives container restart
- [ ] Volume mounts working
- [ ] Database integrity maintained

### ✅ Performance
- [ ] Response times acceptable
- [ ] Memory usage reasonable
- [ ] No memory leaks during operation

## 🛠️ Development Workflow

### Quick Development Cycle
```bash
# 1. Make code changes
# 2. Rebuild and restart
docker-compose up --build -d backend

# 3. Test changes
docker-compose exec backend python import_data.py import

# 4. View logs
docker-compose logs -f backend
```

### Debugging in Container
```bash
# Interactive shell
docker-compose exec backend bash

# Python REPL with app context
docker-compose exec backend python -c "
from app import create_app
app = create_app()
with app.app_context():
    # Your debugging code here
    pass
"
```

## � Troubleshooting Common Issues

### Issue: Backend Container Exits with Code 3

**Symptoms:**
```bash
docker-compose ps
# Shows backend container with "Exit 3" status
investment-tracker_backend_1    /usr/local/bin/docker-entr...    Exit 3
investment-tracker_db_1         docker-entrypoint.sh postgres   Up (healthy)
```

**Diagnostic Steps:**

**Step 1: Check Backend Logs**
```bash
cd ~/investment-tracker
docker-compose logs backend --tail=50
```

**Step 2: Check Container Status**
```bash
docker-compose ps -a
```

**Step 3: Check System Resources (Raspberry Pi)**
```bash
free -h          # Memory usage
df -h            # Disk space
docker stats     # Container resource usage
```

**Common Causes & Solutions:**

**Cause 1: Database Connection Timeout**
```bash
# Solution: Add database wait logic
docker-compose logs db | grep "ready"
# Restart with proper timing
docker-compose down
docker-compose up -d db redis
sleep 10  # Wait for DB to be ready
docker-compose up -d backend
```

**Cause 2: Missing Environment Variables**
```bash
# Check .env file exists
cat .env

# Required variables:
DATABASE_URL=postgresql://user:password@db:5432/investment_tracker
REDIS_URL=redis://redis:6379/0
FLASK_ENV=production
SECRET_KEY=your-secret-key
```

**Cause 3: Python Dependencies Issues**
```bash
# Force rebuild without cache
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d
```

**Cause 4: Memory Limitations (Raspberry Pi)**
```bash
# Check available memory
free -m
# If low memory, restart with resource limits
docker-compose down
docker-compose up -d --scale backend=1
```

**Quick Fix Sequence:**
```bash
# Complete restart with proper timing
docker-compose down -v
docker-compose up -d db redis
sleep 15
docker-compose up -d backend
docker-compose logs -f backend
```

### Issue: CSV Import Fails

**Symptoms:**
- Backend starts but import script fails
- "File not found" errors

**Solutions:**
```bash
# Check file permissions
ls -la data/combined_transactions_updated.csv

# Check volume mount
docker-compose exec backend ls -la /app/data/

# Test import manually
docker-compose exec backend python import_data.py import
```

### Issue: API Endpoints Not Responding

**Symptoms:**
- Backend appears healthy but API calls fail
- Connection refused errors

**Solutions:**
```bash
# Check port mapping
docker-compose ps
# Should show: 0.0.0.0:5000->5000/tcp

# Test from inside container
docker-compose exec backend curl http://localhost:5000/api/health

# Check firewall (Raspberry Pi)
sudo ufw status
```

### Issue: Database Connection Fails

**Symptoms:**
- "Connection refused" to PostgreSQL
- Database not ready errors

**Solutions:**
```bash
# Check database health
docker-compose exec db pg_isready -U postgres

# Reset database
docker-compose down -v
docker-compose up -d db
# Wait for healthy status before starting backend
```

## �💡 Tips and Best Practices

1. **Always check logs first** when troubleshooting
2. **Use health checks** to verify service readiness
3. **Test with fresh volumes** to simulate clean deployments
4. **Monitor resource usage** during testing (especially on Raspberry Pi)
5. **Use .env files** for environment-specific configurations
6. **Keep test data separate** from production data
7. **Regular cleanup** of unused containers and volumes
8. **Start services in order**: DB → Redis → Backend
9. **Allow startup time** especially on slower hardware
10. **Check system resources** before deploying on Raspberry Pi

## 🔗 Useful Commands Reference

```bash
# Essential Docker Compose commands
docker-compose up -d              # Start services in background
docker-compose down               # Stop and remove containers
docker-compose down -v            # Stop and remove volumes
docker-compose build --no-cache   # Force rebuild
docker-compose exec backend bash  # Interactive shell
docker-compose logs -f backend    # Follow logs
docker-compose ps                 # Service status
docker system prune              # Cleanup unused resources
```

This comprehensive testing guide ensures your backend works perfectly in Docker while maintaining all the import functionality for your investment data! 🚀