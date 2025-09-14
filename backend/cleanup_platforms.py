#!/usr/bin/env python3
"""
Platform cleanup script to consolidate duplicate Trading212 platforms
and update transaction references.
"""
import sys
import os
sys.path.append('/app')

from app import create_app, db
from app.models.platform import Platform
from app.models.transaction import Transaction

def cleanup_platforms():
    """Consolidate duplicate platforms and update transactions"""
    app = create_app()
    
    with app.app_context():
        print("=== Platform Cleanup Report ===")
        
        # Get all platforms
        all_platforms = Platform.query.all()
        print(f"Total platforms before cleanup: {len(all_platforms)}")
        
        # Group platforms by normalized name and account type
        platform_groups = {}
        
        for platform in all_platforms:
            # Normalize name for grouping
            normalized_name = platform.name.replace(' ', '').replace('212', '212')
            
            # Standardize common platform names
            name_mappings = {
                'TRADING212': 'Trading212',
                'Trading212': 'Trading212', 
                'trading212': 'Trading212'
            }
            normalized_name = name_mappings.get(normalized_name, normalized_name)
            
            key = (normalized_name, platform.account_type)
            
            if key not in platform_groups:
                platform_groups[key] = []
            platform_groups[key].append(platform)
        
        print(f"Platform groups found: {len(platform_groups)}")
        
        # Process each group
        consolidation_count = 0
        transaction_updates = 0
        
        for (name, account_type), platforms in platform_groups.items():
            if len(platforms) > 1:
                print(f"\nConsolidating {len(platforms)} platforms for {name}_{account_type}")
                
                # Choose the primary platform (first one found, or most recent)
                primary_platform = platforms[0]
                duplicate_platforms = platforms[1:]
                
                print(f"  Primary platform ID: {primary_platform.id}")
                print(f"  Duplicate platform IDs: {[p.id for p in duplicate_platforms]}")
                
                # Update all transactions that reference duplicate platforms
                for dup_platform in duplicate_platforms:
                    transactions = Transaction.query.filter_by(platform_id=dup_platform.id).all()
                    print(f"  Moving {len(transactions)} transactions from platform {dup_platform.id} to {primary_platform.id}")
                    
                    for transaction in transactions:
                        transaction.platform_id = primary_platform.id
                        transaction_updates += 1
                    
                    # Delete the duplicate platform
                    db.session.delete(dup_platform)
                    consolidation_count += 1
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n=== Cleanup Summary ===")
            print(f"Platforms consolidated: {consolidation_count}")
            print(f"Transactions updated: {transaction_updates}")
            print(f"Final platform count: {len(all_platforms) - consolidation_count}")
            
            # Show final platform list
            remaining_platforms = Platform.query.all()
            print("\nRemaining platforms:")
            for platform in remaining_platforms:
                transaction_count = Transaction.query.filter_by(platform_id=platform.id).count()
                print(f"  {platform.id}: {platform.name}_{platform.account_type} ({transaction_count} transactions)")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error during cleanup: {e}")
            return False
            
        return True

if __name__ == "__main__":
    success = cleanup_platforms()
    if success:
        print("\nPlatform cleanup completed successfully!")
    else:
        print("\nPlatform cleanup failed!")
        sys.exit(1)