# Investment Tracker Backend

> A comprehensive Flask-based REST API for investment portfolio management, supporting multi-platform transaction tracking, automated data consolidation, and real-time portfolio analytics.

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-13+-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

## 🏗️ Architecture Overview

The Investment Tracker Backend is a production-ready Flask application designed for managing investment portfolios across multiple trading platforms. It features automated data consolidation, real-time analytics, and comprehensive data integrity management.

### Core Components

```
backend/
├── app/                    # Flask application package
│   ├── api/               # REST API endpoints
│   ├── models/            # SQLAlchemy database models
│   ├── services/          # Business logic services
│   └── tasks/             # Celery background tasks
├── tests/                 # Comprehensive test suite
├── data/                  # CSV import data directory
├── verification/          # Data integrity scripts
└── deployment/            # Docker and deployment configs
```

## 🚀 Features

### 📊 Multi-Platform Portfolio Management
- **Platform Support**: Trading212, Freetrade, Hargreaves Lansdown, AJ Bell
- **Account Types**: ISA, GIA, LISA, SIPP
- **Real-time Holdings**: Automatic position tracking across platforms
- **Fee Management**: Platform-specific fee calculations and tracking

### 📈 Investment Analytics
- **Portfolio Performance**: ROI, gain/loss tracking, time-weighted returns
- **Asset Allocation**: Sector, geography, and currency analysis
- **Dividend Tracking**: Automated dividend recording and yield calculations
- **Price History**: Historical price data integration with Yahoo Finance

### 🔄 Data Management
- **CSV Import**: Automated transaction import from multiple platforms
- **Data Consolidation**: Smart duplicate detection and platform consolidation
- **Data Integrity**: Comprehensive foreign key validation and consistency checks
- **LSE Compatibility**: Full London Stock Exchange integration

### 🛡️ Security & Reliability
- **Authentication**: JWT-based user authentication
- **Data Validation**: Comprehensive input validation and sanitization
- **Error Handling**: Robust error handling with detailed logging
- **Database Integrity**: Foreign key constraints and transaction safety

## 🛠️ Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Framework** | Flask | 2.0+ | Web framework and API |
| **Database** | PostgreSQL | 13+ | Primary data storage |
| **ORM** | SQLAlchemy | 1.4+ | Database abstraction |
| **Cache** | Redis | 6+ | Session and task caching |
| **Tasks** | Celery | 5+ | Background job processing |
| **Finance Data** | yfinance | Latest | Stock price integration |
| **Testing** | pytest | 7+ | Test framework |
| **Deployment** | Docker | 20+ | Containerization |

## 📊 Database Schema

### Core Models

#### Platforms
```sql
platforms (
    id: INTEGER PRIMARY KEY,
    name: VARCHAR(50),           -- Trading212, Freetrade, etc.
    account_type: VARCHAR(20),   -- ISA, GIA, LISA, SIPP
    currency: VARCHAR(3),        -- GBP, USD, EUR
    trading_fee_percentage: DECIMAL(5,4),
    trading_fee_fixed: DECIMAL(10,2),
    fx_fee_percentage: DECIMAL(5,4),
    stamp_duty_applicable: BOOLEAN
)
```

#### Securities
```sql
securities (
    id: INTEGER PRIMARY KEY,
    ticker: VARCHAR(20),         -- ULVR.L, AAPL, etc.
    isin: VARCHAR(12),          -- International identifier
    name: VARCHAR(200),         -- Company name
    exchange: VARCHAR(10),      -- LSE, NASDAQ, NYSE
    currency: VARCHAR(3),       -- GBP, USD, EUR
    country: VARCHAR(2),        -- GB, US, etc.
    sector: VARCHAR(50),        -- Technology, Healthcare
    instrument_type: VARCHAR(20), -- STOCK, ETF, BOND
    yahoo_symbol: VARCHAR(20)   -- Yahoo Finance symbol
)
```

#### Transactions
```sql
transactions (
    id: INTEGER PRIMARY KEY,
    platform_id: INTEGER REFERENCES platforms(id),
    security_id: INTEGER REFERENCES securities(id),
    transaction_type: VARCHAR(10), -- BUY, SELL, DIVIDEND
    quantity: DECIMAL(15,8),
    price: DECIMAL(15,4),
    total_amount: DECIMAL(15,2),
    fees: DECIMAL(15,2),
    transaction_date: DATE,
    created_at: TIMESTAMP
)
```

#### Holdings
```sql
holdings (
    id: INTEGER PRIMARY KEY,
    platform_id: INTEGER REFERENCES platforms(id),
    security_id: INTEGER REFERENCES securities(id),
    quantity: DECIMAL(15,8),
    average_cost: DECIMAL(15,4),
    current_value: DECIMAL(15,2),
    last_updated: TIMESTAMP,
    UNIQUE(platform_id, security_id)
)
```

## 🔌 API Endpoints

### Authentication
```
POST   /api/auth/register     # User registration
POST   /api/auth/login        # User login
POST   /api/auth/logout       # User logout
GET    /api/auth/profile      # Get user profile
```

### Portfolio Management
```
GET    /api/platforms         # List trading platforms
GET    /api/securities        # List securities
GET    /api/transactions      # List transactions
GET    /api/holdings          # List current holdings
GET    /api/portfolios        # List user portfolios
```

### Analytics
```
GET    /api/analytics/performance    # Portfolio performance metrics
GET    /api/analytics/allocation     # Asset allocation breakdown
GET    /api/analytics/dividends      # Dividend history and yields
GET    /api/dashboard               # Dashboard summary data
```

### Data Management
```
POST   /api/import/csv              # Import transaction CSV
GET    /api/import/status           # Check import status
POST   /api/data/consolidate        # Trigger data consolidation
GET    /api/data/integrity          # Data integrity check
```

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

1. **Clone and Start**:
```bash
git clone <repository-url>
cd investment-tracker
docker-compose up -d
```

2. **Verify Health**:
```bash
curl http://localhost:5000/api/health
```

3. **Import Data**:
```bash
docker-compose exec backend python import_data.py import
```

### Option 2: Local Development

1. **Environment Setup**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

2. **Database Setup**:
```bash
# PostgreSQL
createdb investment_tracker
export DATABASE_URL="postgresql://user:pass@localhost/investment_tracker"

# Redis
redis-server
export REDIS_URL="redis://localhost:6379"
```

3. **Application Start**:
```bash
export FLASK_APP=run.py
export FLASK_ENV=development
flask run
```

## 📥 Data Import

### CSV Import Process

The system supports automated CSV import from major UK trading platforms:

1. **Prepare CSV**: Place transaction CSV in `data/` directory
2. **Import**: Run `python import_data.py import`
3. **Verify**: Check data integrity with verification scripts

### Supported Platforms

| Platform | Account Types | CSV Format | Auto-Fees |
|----------|---------------|------------|-----------|
| Trading212 | ISA, GIA | Native export | ✅ |
| Freetrade | ISA, GIA | Native export | ✅ |
| Hargreaves Lansdown | ISA, SIPP, GIA | Native export | ✅ |
| AJ Bell | ISA, LISA, SIPP | Native export | ✅ |

### Data Consolidation

The system automatically:
- **Deduplicates platforms**: Consolidates multiple platform entries
- **Normalizes securities**: Merges duplicate securities by ISIN
- **Validates exchanges**: Corrects LSE/NASDAQ assignments
- **Preserves data**: Maintains all transaction and holding data

## 🧪 Testing

### Comprehensive Test Suite

```bash
# Run all tests
docker-compose exec backend python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/unit/ -v           # Unit tests
python -m pytest tests/integration/ -v    # Integration tests
python -m pytest tests/test_import_data.py # Import functionality
```

### Data Integrity Verification

```bash
# Check platform status
docker-compose exec backend python check_platform_status.py

# Verify holdings integrity
docker-compose exec backend python check_holdings_integrity.py

# Security data verification
docker-compose exec backend python verify_securities.py
```

### Safe Data Cleanup

```bash
# Consolidate duplicate platforms
docker-compose exec backend python safe_cleanup_platforms.py

# Fix security data issues
docker-compose exec backend python safe_fix_securities.py
```

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname
REDIS_URL=redis://host:port/db

# Application
FLASK_ENV=production
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# External APIs
YAHOO_FINANCE_ENABLED=true
ALPHA_VANTAGE_API_KEY=your-api-key
```

### Docker Configuration

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/portfolio
      - REDIS_URL=redis://redis:6379/0
```

## 📊 Monitoring & Maintenance

### Health Checks

```bash
# Service health
curl http://localhost:5000/api/health

# Database connection
docker-compose exec backend python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    print('DB Health:', db.engine.url)
"
```

### Performance Monitoring

```bash
# Container stats
docker stats

# Database performance
docker-compose exec db pg_stat_database

# Redis memory usage
docker-compose exec redis redis-cli info memory
```

### Data Quality Metrics

The system tracks:
- **Platform count**: Should be ~6 (not 100+)
- **Security duplicates**: Minimal ISIN duplicates
- **Foreign key integrity**: Zero broken references
- **Holdings consistency**: All holdings have valid platform/security refs

## 🛡️ Security

### Authentication
- JWT-based stateless authentication
- Password hashing with bcrypt
- Session management with Redis

### Data Protection
- SQL injection prevention via SQLAlchemy
- Input validation and sanitization
- CORS configuration for frontend integration

### Database Security
- Foreign key constraints
- Transaction-safe operations
- Backup and recovery procedures

## 🚀 Deployment

### Production Checklist

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificates installed
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Health checks enabled

### Scaling Considerations

- **Database**: PostgreSQL with read replicas
- **Cache**: Redis cluster for high availability
- **Workers**: Multiple Celery workers for background tasks
- **Load Balancing**: Nginx reverse proxy

## 📈 API Usage Examples

### Get Portfolio Performance
```bash
curl -H "Authorization: Bearer <token>" \
     http://localhost:5000/api/analytics/performance
```

### Import Transaction Data
```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"file_path": "/app/data/transactions.csv"}' \
     http://localhost:5000/api/import/csv
```

### Check Data Integrity
```bash
curl http://localhost:5000/api/data/integrity
```

## 🔗 Related Documentation

- [Docker Testing Guide](../DOCKER_TESTING_README.md)
- [API Documentation](docs/api.md)
- [Database Schema](docs/schema.md)
- [Deployment Guide](docs/deployment.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Investment Tracker Backend** - Built for serious investors who need comprehensive portfolio management across multiple UK trading platforms.

## Environment Variables

Create a `.env` file in the `backend/` directory with the following variables:

```
SECRET_KEY=<your-secret-key>
DATABASE_URL=postgresql://investment_tracker:your_password@localhost/investment_tracker
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Running the Application

1.  **Start Redis:**
    ```bash
    redis-server
    ```
2.  **Start Celery worker:**
    ```bash
    celery -A app.tasks.celery_tasks.celery worker --loglevel=info
    ```
3.  **Run the Flask application:**
    ```bash
    flask run
    ```

## Testing

1.  **Install pytest:**
    ```bash
    pip install pytest
    ```
2.  **Run tests:**
    ```bash
    cd backend
    pytest
    ```