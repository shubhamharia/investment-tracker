#!/bin/bash
# deploy.sh - Main deployment script for Raspberry Pi

set -e  # Exit on any error

echo "? Starting Investment Portfolio Tracker deployment..."

# Configuration
PROJECT_DIR="/home/pi/investment-tracker"
DATA_DIR="${PROJECT_DIR}/data"
BACKUP_DIR="${PROJECT_DIR}/backups"
LOGS_DIR="${PROJECT_DIR}/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Raspberry Pi
check_system() {
    log "Checking system requirements..."
    
    # Check if running on ARM (Raspberry Pi)
    if ! grep -q "ARM\|arm" /proc/cpuinfo; then
        warn "This doesn't appear to be an ARM system (Raspberry Pi). Continuing anyway..."
    fi
    
    # Check available disk space (need at least 2GB)
    available_space=$(df / | tail -1 | awk '{print $4}')
    required_space=2097152  # 2GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        error "Insufficient disk space. Need at least 2GB free."
        exit 1
    fi
    
    # Check memory (recommend at least 1GB)
    memory_mb=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    if [ "$memory_mb" -lt 1024 ]; then
        warn "Less than 1GB RAM detected. Performance may be limited."
    fi
    
    log "System requirements check completed ?"
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    # Update package list
    sudo apt-get update
    
    # Install required packages
    sudo apt-get install -y \
        docker.io \
        docker-compose \
        git \
        curl \
        wget \
        htop \
        nginx \
        certbot \
        python3-certbot-nginx \
        ufw
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    # Enable Docker service
    sudo systemctl enable docker
    sudo systemctl start docker
    
    log "Dependencies installed ?"
}

# Create directory structure
setup_directories() {
    log "Setting up directory structure..."
    
    # Create main directories
    mkdir -p "$PROJECT_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$LOGS_DIR"
    mkdir -p "${PROJECT_DIR}/nginx"
    mkdir -p "${PROJECT_DIR}/ssl"
    
    # Set permissions
    chmod 755 "$PROJECT_DIR"
    chmod 755 "$DATA_DIR"
    chmod 755 "$BACKUP_DIR"
    chmod 755 "$LOGS_DIR"
    
    log "Directory structure created ?"
}

# Clone or update repository
setup_code() {
    log "Setting up application code..."
    
    cd "$(dirname "$PROJECT_DIR")"
    
    if [ -d "$PROJECT_DIR/.git" ]; then
        log "Updating existing repository..."
        cd "$PROJECT_DIR"
        git pull origin main
    else
        warn "Repository clone not implemented. Please manually copy files to $PROJECT_DIR"
        # In a real scenario, you would clone from your git repository:
        # git clone https://github.com/yourusername/investment-tracker.git "$PROJECT_DIR"
    fi
    
    log "Application code ready ?"
}

# Configure environment variables
setup_environment() {
    log "Setting up environment configuration..."
    
    # Create .env file if it doesn't exist
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        cat > "$PROJECT_DIR/.env" << EOF
# Database configuration
POSTGRES_DB=portfolio_db
POSTGRES_USER=portfolio_user
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Flask configuration
FLASK_ENV=production
SECRET_KEY=$(openssl rand -base64 32)

# Redis configuration  
REDIS_URL=redis://redis:6379/0

# API configuration
REACT_APP_API_URL=http://localhost:5000/api

# Timezone
TZ=Europe/London

# Backup configuration
BACKUP_RETENTION_DAYS=30
EOF
        
        log "Environment file created at $PROJECT_DIR/.env"
    else
        log "Environment file already exists"
    fi
    
    # Secure the environment file
    chmod 600 "$PROJECT_DIR/.env"
    
    log "Environment configuration completed ?"
}

# Setup nginx reverse proxy
setup_nginx() {
    log "Setting up Nginx reverse proxy..."
    
    # Create nginx configuration
    cat > "$PROJECT_DIR/nginx/nginx.conf" << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:5000;
    }
    
    upstream frontend {
        server frontend:80;
    }
    
    server {
        listen 80;
        server_name _;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        
        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # API
        location /api/ {
            proxy_pass http://backend/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 300;
        }
        
        # Health checks
        location /health {
            proxy_pass http://backend/health;
            access_log off;
        }
    }
}
EOF
    
    log "Nginx configuration created ?"
}

# Setup firewall
setup_firewall() {
    log "Setting up firewall..."
    
    # Reset UFW
    sudo ufw --force reset
    
    # Default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH (important!)
    sudo ufw allow ssh
    
    # Allow HTTP and HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Allow VPN if configured
    if command -v openvpn &> /dev/null; then
        sudo ufw allow 1194/udp
    fi
    
    # Enable firewall
    sudo ufw --force enable
    
    log "Firewall configured ?"
}

# Copy CSV data
setup_data() {
    log "Setting up data files..."
    
    # Check if CSV file exists in current directory
    if [ -f "combined_transactions_updated.csv" ]; then
        cp "combined_transactions_updated.csv" "$DATA_DIR/"
        log "CSV data file copied to $DATA_DIR"
    else
        warn "CSV file not found in current directory"
        log "Please copy your combined_transactions_updated.csv to $DATA_DIR/"
    fi
    
    log "Data setup completed ?"
}

# Start services
start_services() {
    log "Starting services..."
    
    cd "$PROJECT_DIR"
    
    # Pull latest images
    docker-compose pull
    
    # Build custom images
    docker-compose build
    
    # Start services
    docker-compose up -d
    
    # Wait for services to start
    log "Waiting for services to start..."
    sleep 30
    
    # Check service status
    if docker-compose ps | grep -q "Up"; then
        log "Services started successfully ?"
    else
        error "Some services failed to start. Check logs with: docker-compose logs"
        return 1
    fi
}

# Import initial data
import_data() {
    log "Importing initial data..."
    
    cd "$PROJECT_DIR"
    
    # Wait for database to be ready
    log "Waiting for database to be ready..."
    docker-compose exec -T backend python -c "
import time
import psycopg2

for i in range(30):
    try:
        conn = psycopg2.connect(
            host='db',
            database='portfolio_db',
            user='portfolio_user',
            password='portfolio_pass'  # Make sure this matches your docker-compose.yml
        )
        print('/var/run/postgresql:5432 - accepting connections')
        conn.close()
        break
    except psycopg2.OperationalError as e:
        if i == 29:
            raise
        time.sleep(2)
"
    
    # Run data import with environment variables
    log "Running data import..."
    docker-compose exec -T \
        -e POSTGRES_DB=portfolio_db \
        -e POSTGRES_USER=portfolio_user \
        -e POSTGRES_PASSWORD=portfolio_pass \
        backend python import_data.py import
    
    log "Data import completed ?"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Create monitoring script
    cat > "$PROJECT_DIR/monitor.sh" << 'EOF'
#!/bin/bash

# Monitor script for Investment Tracker

LOG_FILE="/home/pi/investment-tracker/logs/monitor.log"
ALERT_EMAIL=""  # Set this to receive email alerts

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

check_containers() {
    cd /home/pi/investment-tracker
    
    # Check if all containers are running
    down_containers=$(docker-compose ps -q | xargs docker inspect -f '{{.Name}} {{.State.Status}}' | grep -v running | wc -l)
    
    if [ "$down_containers" -gt 0 ]; then
        log_message "ERROR: $down_containers containers are down"
        docker-compose up -d
        return 1
    fi
    
    return 0
}

check_disk_space() {
    # Check disk space (alert if less than 1GB)
    available_kb=$(df / | tail -1 | awk '{print $4}')
    available_gb=$((available_kb / 1024 / 1024))
    
    if [ "$available_gb" -lt 1 ]; then
        log_message "WARNING: Low disk space - ${available_gb}GB remaining"
        return 1
    fi
    
    return 0
}

check_memory() {
    # Check memory usage (alert if over 90%)
    memory_usage=$(free | awk 'NR==2{printf "%.0f", $3/$2*100}')
    
    if [ "$memory_usage" -gt 90 ]; then
        log_message "WARNING: High memory usage - ${memory_usage}%"
        return 1
    fi
    
    return 0
}

main() {
    log_message "Starting health checks"
    
    check_containers
    container_status=$?
    
    check_disk_space
    disk_status=$?
    
    check_memory
    memory_status=$?
    
    if [ $container_status -eq 0 ] && [ $disk_status -eq 0 ] && [ $memory_status -eq 0 ]; then
        log_message "All checks passed ?"
    else
        log_message "Health checks failed"
        # In a real scenario, you might send an email or push notification here
        # send_alert
    fi
    
    return 0
}

# Run the main function
main

# Call a cleanup function
# cleanup

# End of script
EOF
log "Monitoring script created ?"
}

# Main script
main() {
    check_system
    install_dependencies
    setup_directories
    setup_code
    setup_environment
    setup_nginx
    setup_firewall
    setup_data
    start_services
    import_data
    setup_monitoring
    log "Deployment completed ?"
}

# Execute main function
main
