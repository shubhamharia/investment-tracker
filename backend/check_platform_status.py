#!/usr/bin/env python3
"""
Script to check current platform situation in the database
"""
import sys
import os
sys.path.append('/app')

from app import create_app, db
from app.models.platform import Platform
from app.models.transaction import Transaction

def check_platforms():
    """Check current platform situation"""
    app = create_app()
    
    with app.app_context():
        print("=== Current Platform Status ===")
        
        # Get all platforms
        platforms = Platform.query.all()
        print(f"Total platforms: {len(platforms)}")
        
        print("\nPlatform details:")
        for platform in platforms:
            transaction_count = Transaction.query.filter_by(platform_id=platform.id).count()
            print(f"ID {platform.id}: '{platform.name}' + '{platform.account_type}' ({transaction_count} transactions)")
        
        # Group by normalized name
        print("\nGrouped by normalized name:")
        name_groups = {}
        for platform in platforms:
            normalized = platform.name.replace(' ', '')
            if normalized not in name_groups:
                name_groups[normalized] = []
            name_groups[normalized].append(platform)
        
        for name, group in name_groups.items():
            print(f"  {name}: {len(group)} platforms")
            for platform in group:
                transaction_count = Transaction.query.filter_by(platform_id=platform.id).count()
                print(f"    - {platform.account_type}: {transaction_count} transactions")

if __name__ == "__main__":
    check_platforms()