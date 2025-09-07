# Investment Tracker

A full-stack application to track investments across multiple platforms.

## Project Structure
```
investment-tracker/
├── backend/             # Flask API server
├── frontend/           # React frontend
├── nginx/             # Nginx configuration
├── docker-compose.yml # Docker configuration
├── deploy.sh         # Deployment script
└── README.md        # This file
```

## Prerequisites
- Python 3.11+
- Node.js 16+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose

## Development Setup

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

### Local Deployment
```bash
./deploy.sh
```

### Production Deployment
1. Update environment variables in `.env`
2. Run deployment script:
```bash
./deploy.sh --prod
```

## API Documentation

### Endpoints
- `/api/platforms` - Platform management
- `/api/securities` - Security management
- `/api/transactions` - Transaction management

### Authentication
Bearer token required for all API endpoints except health check.

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