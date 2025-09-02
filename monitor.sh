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
