# Investment Tracker

A full-stack application to track investments across multiple platforms with support for LSE (London Stock Exchange) securities and comprehensive Docker deployment.

## Project Structure
```
investment-tracker/
├── backend/                    # Flask API server
│   ├── app/                   # Main application code
│   ├── tests/                 # Comprehensive test suite
│   ├── import_data.py         # CSV data import utility
│   └── docker-entrypoint.sh   # Docker initialization
├── frontend/                  # React frontend
├── nginx/                     # Nginx configuration
├── data/                      # CSV data files
├── docker-compose.yml         # Production Docker config
├── docker-compose.test.yml    # Testing Docker config
├── DOCKER_TESTING_README.md   # Docker testing guide
├── test.ps1                   # Comprehensive test script
└── README.md                  # This file
```

## Prerequisites

### For Local Development
- Python 3.11+
- Node.js 16+
- PostgreSQL 13+
- Redis 6+

### For Docker Deployment (Recommended)
- Docker 20.0+
- Docker Compose 2.0+

## Quick Start with Docker 🐳

## Backend Hardening & Test Reliability

- All backend API endpoints now return robust status codes and JSON shapes matching integration tests.
- Deterministic yfinance shim avoids network flakiness in CI and test runs.
- Portfolio, transaction, and holding creation now accept compatibility keys and handle missing fields gracefully.
- POST `/api/portfolios/<id>/dividends` endpoint added for dividend creation.
- Portfolio value endpoint now includes `currency` key.
- Platform normalization and cleanup scripts included for duplicate platform records.

## Running Backend Tests in Docker Compose

To run the full backend test suite inside Docker Compose:

```bash
cd investment-tracker
docker-compose run --rm --entrypoint "" backend sh -c "cd /app && pytest -q"
```

To run a single test module:

```bash
docker-compose run --rm --entrypoint "" backend sh -c "cd /app && pytest tests/integration/test_api.py -q"
```

All integration tests should pass after the above hardening and fixes.

### 1. Clone and Setup
```bash
git clone <repository-url>
cd investment-tracker
```

### 2. Prepare Data (Optional)
Place your CSV transaction file in the `data/` directory:
```bash
# Your CSV file should be: data/combined_transactions_updated.csv
```

### 3. Start Services
```bash
# Start all services
docker-compose up -d

# Or start with automatic CSV import
AUTO_IMPORT_CSV=true docker-compose up -d
```

### 4. Verify Deployment
```bash
# Run comprehensive tests
./test.ps1

# Or check services manually
docker-compose ps
curl http://localhost:5000/api/health
```

Your application will be available at:
- **API**: http://localhost:5000
- **Frontend**: http://localhost:3000 (when frontend is running)

## Docker Operations 🐳

### Service Management
```bash
# Start all services
docker-compose up -d

# Start with CSV auto-import
AUTO_IMPORT_CSV=true docker-compose up -d

# View service status
docker-compose ps

# Stop services
docker-compose down

# Rebuild and start
docker-compose up -d --build
```

### Data Import
```bash
# Import CSV data manually
docker-compose exec backend python import_data.py import

# Check import status
docker-compose exec backend python import_data.py status

# Import with CLI options
docker-compose exec backend python import_data.py import --file /app/data/your_file.csv
```

### Monitoring and Logs
```bash
# View all logs
docker-compose logs -f

# View backend logs only
docker-compose logs -f backend

# Check container stats
docker stats

# Health check
curl http://localhost:5000/api/health
```

### Troubleshooting Common Issues

#### Backend Container Exit 3 Error
```bash
# Check backend logs
docker-compose logs backend --tail=50

# Restart backend service
docker-compose restart backend

# Full rebuild if needed
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d
```

#### Database Connection Issues
```bash
# Check database status
docker-compose exec db pg_isready

# Restart database
docker-compose restart db

# Check environment variables
docker-compose exec backend env | grep DATABASE
```

#### CSV Import Issues
```bash
# Verify CSV file exists
docker-compose exec backend ls -la /app/data/

# Check file permissions
docker-compose exec backend stat /app/data/combined_transactions_updated.csv

# Test import script directly
docker-compose exec backend python -c "from import_data import get_default_csv_path; print(get_default_csv_path())"
```

## Development Setup (Alternative to Docker)

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Linux/Mac
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
```

### Database
```bash
# Create database
createdb investment_tracker

# Run migrations
cd backend
flask db upgrade
```

## Testing

### Comprehensive Docker Testing
```bash
# Run all Docker tests (recommended)
./test.ps1

# Run Docker tests and keep services running
./test.ps1 -KeepRunning

# Run without rebuilding containers
./test.ps1 -SkipBuild

# Show help
./test.ps1 -Help
```

### Manual Testing

### Backend Tests
```bash
cd backend
python -m pytest  # Run all tests
python -m pytest tests/test_api  # Run API tests only
python -m pytest --cov=app  # Run with coverage
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Deployment

### Docker Deployment (Recommended)

#### Production Deployment
```bash
# 1. Clone repository
git clone <repository-url>
cd investment-tracker

# 2. Set up environment variables
cp .env.example .env
# IMPORTANT: edit `.env` and replace the placeholder secrets and passwords
# with secure values before deploying to production. Never commit `.env`.

# 3. Deploy (build and start services)
docker-compose up -d --build

# 4. Import data (if CSV available)
docker-compose exec backend python import_data.py import

# 5. Verify deployment
./test.ps1 docker-test
```

#### Raspberry Pi Deployment
```bash
# Check system resources
free -h
df -h

# Start services with resource limits
docker-compose up -d

# Monitor resource usage
docker stats --no-stream

# Check service status
docker-compose ps
```

### Troubleshooting Deployment Issues

#### Service Status Check
```bash
# Check all services
docker-compose ps

# Expected healthy output:
# backend_1    Up (healthy)   0.0.0.0:5000->5000/tcp
# db_1         Up (healthy)   0.0.0.0:5432->5432/tcp
# redis_1      Up            6379/tcp
```

#### Common Exit Codes
- **Exit 0**: Normal shutdown
- **Exit 1**: General application error
- **Exit 3**: Configuration/database connection error
- **Exit 125**: Docker daemon error

#### Recovery Steps
```bash
# Complete restart sequence
docker-compose down
docker-compose up -d db redis    # Start dependencies first
sleep 10                         # Wait for DB ready
docker-compose up -d backend     # Start backend
docker-compose logs -f backend   # Monitor startup
```

### Local Development Deployment
```bash
./deploy.sh
```

### Production Environment Variables
Create a `.env` file with the following variables:
```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@db:5432/investment_tracker
POSTGRES_DB=investment_tracker
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key

# CSV Import Configuration
AUTO_IMPORT_CSV=false  # Set to true for automatic import on startup
CSV_FILE_PATH=/app/data/combined_transactions_updated.csv

# API Configuration
API_RATE_LIMIT=1000 per hour
CORS_ORIGINS=*

# Logging
LOG_LEVEL=INFO
```

Security notes:
- Do not commit `.env` into version control. Use a secret manager for production.
- Use strong random values for `SECRET_KEY` and `JWT_SECRET_KEY` (at least 32 bytes).
- If running in public networks, restrict `CORS_ORIGINS` and use HTTPS via a reverse proxy (nginx or cloud load balancer).

## Features

### Core Functionality
- **Multi-platform Investment Tracking**: Support for various trading platforms
- **LSE Stock Integration**: Real-time data for London Stock Exchange securities
- **CSV Data Import**: Bulk transaction import with relative path support
- **Portfolio Analytics**: Performance tracking and analysis
- **RESTful API**: Complete API for all operations

### Docker Features
- **Cross-platform Compatibility**: Relative file paths for Windows/Linux/macOS
- **Auto-import Capability**: Automatic CSV import on container startup
- **Health Monitoring**: Built-in health checks and monitoring
- **Volume Mounting**: Persistent data storage
- **Multi-service Orchestration**: PostgreSQL, Redis, and backend coordination

### Security Features
- **JWT Authentication**: Secure API access
- **Input Validation**: Comprehensive data validation
- **SQL Injection Protection**: SQLAlchemy ORM protection
- **Rate Limiting**: API rate limiting protection

## API Documentation

### Health Check
```bash
GET /api/health
# Response: {"status": "healthy", "timestamp": "2025-09-14T10:00:00Z"}
```

### Core Endpoints
- **Platforms**: `/api/platforms` - Trading platform management
- **Securities**: `/api/securities` - Security/stock management  
- **Transactions**: `/api/transactions` - Transaction management
- **Portfolios**: `/api/portfolios` - Portfolio management
- **Holdings**: `/api/holdings` - Current holdings
- **Performance**: `/api/performance` - Portfolio performance analytics
- **Dividends**: `/api/dividends` - Dividend tracking

### Authentication
```bash
# All endpoints except /api/health require JWT token
Authorization: Bearer <your-jwt-token>
```

### CSV Import API
```bash
# Import transactions from CSV
POST /api/import/csv
Content-Type: multipart/form-data

# Check import status
GET /api/import/status

# Example curl command
curl -X POST http://localhost:5000/api/import/csv \
  -H "Authorization: Bearer <token>" \
  -F "file=@data/combined_transactions_updated.csv"
```

## File Structure Details

### Backend Structure
```
backend/
├── app/
│   ├── api/                 # API endpoints
│   │   ├── auth.py         # Authentication
│   │   ├── platforms.py    # Platform management
│   │   ├── securities.py   # Security management
│   │   ├── transactions.py # Transaction management
│   │   └── ...
│   ├── models/             # Database models
│   │   ├── user.py        # User model
│   │   ├── transaction.py # Transaction model
│   │   ├── security.py    # Security model
│   │   └── ...
│   ├── services/          # Business logic
│   │   ├── portfolio_service.py
│   │   ├── price_service.py
│   │   └── ...
│   └── tasks/             # Background tasks
├── tests/                 # Comprehensive test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── conftest.py       # Test configuration
├── import_data.py        # CSV import utility
└── docker-entrypoint.sh  # Docker startup script
```

### CSV Data Format
```csv
Date,Platform,Type,Ticker,Quantity,Price,Currency,Fees,Total
2025-01-15,Trading212,BUY,ULVR.L,10,45.50,GBP,0.00,455.00
2025-01-16,Trading212,SELL,ULVR.L,5,46.00,GBP,0.00,230.00
```

### Required CSV Columns
- **Date**: Transaction date (YYYY-MM-DD)
- **Platform**: Trading platform name
- **Type**: BUY/SELL
- **Ticker**: Security ticker symbol (LSE format: SYMBOL.L)
- **Quantity**: Number of shares
- **Price**: Price per share
- **Currency**: Currency code (GBP, USD, EUR)
- **Fees**: Transaction fees
- **Total**: Total transaction amount

## Directory Structure Details

### Backend
- `app/` - Main application code
  - `api/` - API endpoints
  - `models/` - Database models
  - `services/` - Business logic
- `tests/` - Test files
  - `test_api/` - API tests
  - `test_data/` - Test data files

### Frontend
- `src/` - React components and logic
- `public/` - Static files

## Contributing
1. Create feature branch
2. Write tests
3. Submit pull request

## License
MIT License