# Investment Portfolio Tracker - Setup Guide

A comprehensive investment tracking system designed for Raspberry Pi deployment with multi-platform support, real-time price updates, and detailed analytics.

## 🏗️ Architecture Overview

- **Backend**: Python Flask + PostgreSQL + Redis + Celery
- **Frontend**: React with modern UI components
- **Price Data**: Yahoo Finance (primary) + Alpha Vantage (backup)
- **Deployment**: Docker containers with Nginx reverse proxy
- **Monitoring**: Health checks + automated backups
- **Security**: Firewall, SSL support, secure environment variables

## 📋 Prerequisites

### Hardware Requirements (Raspberry Pi)
- **RAM**: Minimum 2GB (4GB recommended)
- **Storage**: 16GB+ SD card (32GB recommended)
- **Network**: Ethernet/WiFi with internet access

### Software Requirements
- Raspberry Pi OS (64-bit recommended)
- Docker and Docker Compose
- Git
- SSH access configured

## 🚀 Quick Start

### 1. Clone and Prepare Files

```bash
# SSH into your Raspberry Pi
ssh pi@your-pi-ip-address

# Create project directory
mkdir -p /home/pi/investment-tracker
cd /home/pi/investment-tracker

# Copy the deployment script (from the artifacts above)
# Save deploy.sh, docker-compose.yml, and all configuration files
```

### 2. Prepare Your Data

```bash
# Copy your CSV file to the data directory
cp combined_transactions_updated.csv /home/pi/investment-tracker/data/

# If you have additional CSVs (dividends, fees), place them in data/ as well
```

### 3. Run Deployment

```bash
# Make the deployment script executable
chmod +x deploy.sh

# Run full deployment
./deploy.sh deploy

# Or with SSL (if you have a domain)
./deploy.sh deploy yourdomain.com
```

### 4. Verify Installation

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Test API health
curl http://localhost:5000/health

# Access frontend
# Open browser to http://your-pi-ip-address
```

## 📁 Project Structure

```
/home/pi/investment-tracker/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── import_data.py         # Data import utilities
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile            # Backend container config
│   └── config.py             # Application configuration
├── frontend/
│   ├── src/
│   │   ├── InvestmentTracker.js  # Main React component
│   │   └── index.js          # React entry point
│   ├── package.json          # Node dependencies
│   ├── Dockerfile           # Frontend container config
│   └── nginx.conf           # Nginx configuration
├── data/
│   └── combined_transactions_updated.csv  # Your transaction data
├── backups/                  # Database backups
├── logs/                     # Application logs
├── nginx/
│   └── nginx.conf           # Reverse proxy config
├── docker-compose.yml       # Container orchestration
├── deploy.sh               # Deployment script
├── .env                    # Environment variables
└── README.md              # This file
```

## 🔧 Configuration

### Environment Variables (.env)

The deployment script creates a `.env` file with secure defaults:

```bash
# Database
POSTGRES_DB=portfolio_db
POSTGRES_USER=portfolio_user
POSTGRES_PASSWORD=<generated-secure-password>

# Flask
FLASK_ENV=production
SECRET_KEY=<generated-secure-key>

# Redis
REDIS_URL=redis://redis:6379/0

# API
REACT_APP_API_URL=http://localhost:5000/api

# Timezone
TZ=Europe/London
```

### Platform Fee Configuration

The system automatically configures fees for supported platforms:

- **Trading212**: 0% trading fees, 0.15% FX fees
- **Freetrade**: 0% trading fees, 0.45% FX fees  
- **Hargreaves Lansdown**: £11.95 trading fees, 1% FX fees
- **AJ Bell**: £9.95 trading fees, 0.5% FX fees

## 📊 Features

### Dashboard
- **Portfolio Overview**: Total value, cost, gain/loss
- **Platform Breakdown**: Holdings across different brokers
- **Asset Allocation**: Visual charts and analytics
- **Real-time Updates**: Prices update every 5-10 minutes

### Holdings Management
- **Current Positions**: Quantity, average cost, current value
- **Performance Tracking**: Unrealized gains/losses
- **Multi-currency Support**: GBP, USD, EUR with FX conversion

### Transaction History
- **Complete Record**: All buy/sell transactions
- **Fee Tracking**: Trading fees, FX fees, stamp duty
- **Filtering & Search**: By date, platform, security

### Price Data
- **Real-time Prices**: Yahoo Finance (primary source)
- **Historical Data**: Back to 2022 for performance calculation
- **Fallback Sources**: Alpha Vantage, Financial Modeling Prep
- **Update Frequency**: 5 minutes (market hours), hourly (off-hours)

## 🛠️ Management Commands

### Daily Operations

```bash
# Check status
./deploy.sh status

# View logs
./deploy.sh logs [service-name]

# Restart services
./deploy.sh restart

# Update application
./deploy.sh update

# Create backup
./deploy.sh backup
```

### Data Management

```bash
# Import new CSV data
docker-compose exec backend python import_data.py import --csv-file /app/data/new_data.csv

# Update security names
docker-compose exec backend python import_data.py update-names

# Validate data integrity
docker-compose exec backend python import_data.py validate

# Manual price refresh
docker-compose exec backend python -c "from app import update_prices; update_prices.delay()"
```

### Database Operations

```bash
# Access database
docker-compose exec db psql -U portfolio_user -d portfolio_db

# Create backup
docker-compose exec db pg_dump -U portfolio_user portfolio_db > backup.sql

# Restore backup
docker-compose exec -T db psql -U portfolio_user -d portfolio_db < backup.sql
```

## 🔒 Security

### Network Security
- **Firewall**: UFW configured to allow only necessary ports
- **VPN Access**: Designed for VPN-only access
- **SSL Support**: Optional Let's Encrypt integration
- **Secure Headers**: HTTPS, HSTS, XSS protection

### Data Security
- **Environment Variables**: Secure storage of credentials
- **Database Encryption**: PostgreSQL with secure passwords
- **Backup Encryption**: Compressed backups with retention policy
- **Access Control**: No public internet exposure by design

## 📈 Monitoring & Maintenance

### Automated Monitoring

The system includes automated monitoring:

```bash
# Monitor script runs every 5 minutes via cron
*/5 * * * * /home/pi/investment-tracker/monitor.sh

# Daily backups at 2 AM
0 2 * * * /home/pi/investment-tracker/backup.sh

# Price updates (handled by Celery Beat)
# - Every 5 minutes during market hours (8 AM - 4 PM, Mon-Fri)
# - Every hour outside market hours
```

### Log Monitoring

```bash
# Application logs
tail -f /home/pi/investment-tracker/logs/portfolio.log

# Container logs
docker-compose logs -f [backend|frontend|db|redis|celery_worker]

# System monitoring
htop
df -h
docker system df
```

### Performance Optimization

For Raspberry Pi deployment:

```bash
# Increase swap (if needed)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# GPU memory split (reduce if no desktop needed)
sudo raspi-config  # Advanced Options > Memory Split > 16

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable hciuart
```

## 🐛 Troubleshooting

### Common Issues

**Containers won't start:**
```bash
# Check Docker status
sudo systemctl status docker

# Check disk space
df -h

# Check memory
free -h

# Check logs
docker-compose logs
```

**Database connection errors:**
```bash
# Wait for database to start
docker-compose exec backend python -c "
import psycopg2
import os
conn = psycopg2.connect(
    host='db',
    database=os.environ['POSTGRES_DB'],
    user=os.environ['POSTGRES_USER'],
    password=os.environ['POSTGRES_PASSWORD']
)
print('Database connected!')
"
```

**Price update failures:**
```bash
# Check internet connectivity
curl -I https://query1.finance.yahoo.com

# Manual price update test
docker-compose exec backend python -c "
from app import PriceService
print(PriceService.fetch_current_price('AAPL'))
"
```

**High memory usage:**
```bash
# Restart services to free memory
docker-compose restart

# Check container resource usage
docker stats

# Reduce Celery workers if needed
# Edit docker-compose.yml: --workers 1
```

## 🔄 Updates & Maintenance

### Regular Updates

```bash
# Weekly system updates
sudo apt update && sudo apt upgrade -y

# Monthly Docker cleanup
docker system prune -f
docker volume prune -f

# Quarterly data validation
docker-compose exec backend python import_data.py validate
```

### Adding New Data

When you get new transaction data:

1. **Add CSV to data directory:**
   ```bash
   cp new_transactions.csv /home/pi/investment-tracker/data/
   ```

2. **Import new data:**
   ```bash
   docker-compose exec backend python import_data.py import --csv-file /app/data/new_transactions.csv
   ```

3. **Recalculate holdings:**
   ```bash
   docker-compose exec backend python -c "from app import PortfolioService; PortfolioService.calculate_holdings()"
   ```

4. **Update prices:**
   ```bash
   docker-compose exec backend python -c "from app import update_prices; update_prices.delay()"
   ```

## 📞 Support

### Getting Help

1. **Check logs first:**
   ```bash
   ./deploy.sh logs
   ```

2. **Validate configuration:**
   ```bash
   docker-compose config
   ```

3. **Test individual components:**
   ```bash
   # Backend health
   curl http://localhost:5000/health
   
   # Database connection
   docker-compose exec db pg_isready -U portfolio_user
   
   # Redis connection
   docker-compose exec redis redis-cli ping
   ```

### Performance Monitoring

Monitor your Pi's performance:

```bash
# Resource usage dashboard
htop

# Container resource usage
docker stats

# Disk usage
df -h
du -sh /home/pi/investment-tracker/*

# Network usage
iftop
```

---

## 🎉 You're All Set!

Your investment portfolio tracker is now running on your Raspberry Pi with:

- ✅ **Multi-platform support** for all your brokers
- ✅ **Real-time price updates** every 5-10 minutes
- ✅ **Secure VPN-only access** as requested
- ✅ **Automated backups** and monitoring
- ✅ **Historical performance tracking** back to 2022
- ✅ **Professional web interface** accessible from any device

Access your portfolio at: `http://your-pi-ip-address`

The system will continue to update prices automatically and maintain your portfolio data securely on your Raspberry Pi!