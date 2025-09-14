# Docker Comprehensive Testing Guide

This guide provides a complete testing methodology for the Investment Tracker backend in Docker, including data integrity validation and comprehensive system verification.

## 📋 Prerequisites

- Docker Desktop/Docker Engine running
- Docker Compose v2+
- SSH access to deployment environment
- CSV file in `data/` directory

## 🧪 Comprehensive Test Suite

### Test Categories
1. **Basic Health Tests** - Container status, database connectivity
2. **Data Integrity Tests** - Platform consolidation, security validation  
3. **API Endpoint Tests** - REST API functionality
4. **Performance Tests** - Query performance, resource usage
5. **Integration Tests** - CSV import, cross-service operations
6. **Security Tests** - Authentication, authorization
7. **Edge Case Tests** - Error handling, boundary conditions

## 🚀 Quick Start Testing

### Step 1: Service Health Check
```bash
# Check all services are running
docker-compose ps

# Verify backend health
curl http://localhost:5000/api/health

# Test database connection
docker-compose exec backend python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    print('Database connection:', db.engine.url)
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print('Tables:', tables)
    print('✅ Database connection working!')
"
```

### Step 2: Data Quality Verification
```bash
# Run comprehensive data quality check
docker-compose exec backend python -c "
from app import create_app, db
from app.models import Transaction, Security, Platform, Holding
from collections import Counter
app = create_app()
with app.app_context():
    print('🧪 COMPREHENSIVE DATA QUALITY CHECK')
    print('=' * 50)
    
    # Basic counts
    platforms = Platform.query.count()
    securities = Security.query.count() 
    transactions = Transaction.query.count()
    holdings = Holding.query.count()
    print(f'Platforms: {platforms} (should be 6)')
    print(f'Securities: {securities} (should be ~77)')
    print(f'Transactions: {transactions}')
    print(f'Holdings: {holdings}')
    
    # Platform analysis
    all_platforms = Platform.query.all()
    platform_names = [p.name for p in all_platforms]
    name_counts = Counter(platform_names)
    duplicates = [name for name, count in name_counts.items() if count > 1]
    print(f'Duplicate platforms: {duplicates}')
    
    # Foreign key integrity
    all_holdings = Holding.query.all()
    valid_platform_ids = {p.id for p in Platform.query.all()}
    valid_security_ids = {s.id for s in Security.query.all()}
    
    invalid_platforms = sum(1 for h in all_holdings if h.platform_id not in valid_platform_ids)
    invalid_securities = sum(1 for h in all_holdings if h.security_id not in valid_security_ids)
    
    print(f'Holdings with invalid platform refs: {invalid_platforms}')
    print(f'Holdings with invalid security refs: {invalid_securities}')
    print('✅ Data quality check completed!')
"
```

### Step 3: Run Existing Verification Scripts
```bash
# Holdings integrity check
docker-compose exec backend python /app/check_holdings_integrity.py

# Platform status check  
docker-compose exec backend python /app/check_platform_status.py

# Securities verification
docker-compose exec backend python /app/verify_securities.py
```

## 🔧 Data Quality Management

### Safe Cleanup Scripts (if duplicates found)
```bash
# If platform count > 6, run cleanup
docker-compose exec backend python /app/safe_cleanup_platforms.py

# Fix security data issues
docker-compose exec backend python /app/safe_fix_securities.py

# Verify cleanup worked
docker-compose exec backend python -c "
from app import create_app, db
from app.models import Platform, Security
app = create_app()
with app.app_context():
    print(f'Platforms after cleanup: {Platform.query.count()}')
    print(f'Securities after cleanup: {Security.query.count()}')
"
```

## 🌐 API Testing

### Test Core Endpoints
```bash
# Test platforms API
curl -s http://localhost:5000/api/platforms | head -c 200

# Test securities API  
curl -s http://localhost:5000/api/securities | head -c 200

# Test API module imports
docker-compose exec backend python -c "
try:
    from app.api.platforms import platforms_bp
    from app.api.securities import securities_bp
    from app.api.transactions import transactions_bp
    from app.api.holdings import holdings_bp
    print('✅ All API modules imported successfully')
except Exception as e:
    print(f'❌ API import failed: {e}')
"
```

## 📊 CSV Import Testing

### Verify Import Functionality
```bash
# Check CSV file mount
docker-compose exec backend ls -la /app/data/

# Test CSV import logic
docker-compose exec backend python -c "
import sys, os
sys.path.insert(0, '/app')
csv_path = '/app/data/combined_transactions_updated.csv'
print(f'CSV file exists: {os.path.exists(csv_path)}')

from import_data import get_default_csv_path
default_path = get_default_csv_path()
print(f'Default CSV path: {default_path}')
print(f'Path exists: {os.path.exists(default_path)}')
print('✅ CSV import paths working correctly')
"
```

## 📈 Performance Testing

### LSE Stock Compatibility
```bash
# Test yfinance integration for LSE stocks
docker-compose exec backend python -c "
import yfinance as yf
stocks = ['ULVR.L', 'HSBA.L', 'SHEL.L']
print('Testing LSE stock data retrieval:')
for stock in stocks:
    try:
        ticker = yf.Ticker(stock)
        info = ticker.info
        print(f'  {stock}: {info.get(\"longName\", \"Unknown\")}')
    except Exception as e:
        print(f'  {stock}: Error - {e}')
"
```

## 🚨 Troubleshooting

### Common Issues

**Issue: Platform Duplicates**
```bash
# Symptoms: Platform count > 6
# Solution: Run safe cleanup scripts (see Data Quality Management section)
```

**Issue: Backend Container Exits**
```bash
# Check logs
docker-compose logs backend --tail=50

# Common fix: Restart with proper timing
docker-compose down
docker-compose up -d db redis
sleep 15
docker-compose up -d backend
```

**Issue: Database Connection Failed**
```bash
# Check database health
docker-compose exec db pg_isready -U postgres

# Reset if needed
docker-compose down -v
docker-compose up -d
```

## ✅ Test Checklist

### Essential Verification Points
- [ ] All containers running (`docker-compose ps`)
- [ ] Backend health endpoint responding
- [ ] Database connection working
- [ ] Platform count = 6 (not 114+)
- [ ] No foreign key integrity issues
- [ ] CSV file accessible in container
- [ ] API endpoints responding
- [ ] LSE stock data retrieval working

### Post-Import Validation
- [ ] Transaction count preserved
- [ ] Holdings integrity maintained  
- [ ] No duplicate platforms created
- [ ] Security exchange assignments correct
- [ ] All API modules importable

## 🔄 Quick Reset Procedure
```bash
# Complete environment reset
docker-compose down -v
docker-compose up -d db redis
sleep 15
docker-compose up -d backend

# Wait for health
curl http://localhost:5000/api/health

# Run cleanup if needed
docker-compose exec backend python /app/safe_cleanup_platforms.py
docker-compose exec backend python /app/safe_fix_securities.py
```

This streamlined testing guide focuses on the essential verification steps that ensure your investment tracker is running correctly with clean, consolidated data! 🚀