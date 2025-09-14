#!/usr/bin/env python3
"""
Safe platform cleanup script that handles holdings table properly
"""
import sys
import os
sys.path.append('/app')

from app import create_app, db
from app.models.platform import Platform
from app.models.transaction import Transaction
from app.models.holding import Holding

def safe_cleanup_platforms():
    """Safely consolidate duplicate platforms handling holdings table"""
    app = create_app()
    
    with app.app_context():
        print("=== SAFE Platform Cleanup ===")
        
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
        holdings_updates = 0
        
        for (name, account_type), platforms in platform_groups.items():
            if len(platforms) > 1:
                print(f"\nConsolidating {len(platforms)} platforms for {name}_{account_type}")
                
                # Choose the primary platform (one with most transactions)
                primary_platform = None
                max_transactions = 0
                
                for platform in platforms:
                    tx_count = Transaction.query.filter_by(platform_id=platform.id).count()
                    if tx_count > max_transactions:
                        max_transactions = tx_count
                        primary_platform = platform
                
                # If no transactions found, use first platform
                if primary_platform is None:
                    primary_platform = platforms[0]
                
                duplicate_platforms = [p for p in platforms if p.id != primary_platform.id]
                
                print(f"  Primary platform ID: {primary_platform.id} ({max_transactions} transactions)")
                print(f"  Duplicate platform IDs: {[p.id for p in duplicate_platforms]}")
                
                # Update all transactions that reference duplicate platforms
                for dup_platform in duplicate_platforms:
                    # Update transactions
                    transactions = Transaction.query.filter_by(platform_id=dup_platform.id).all()
                    print(f"  Moving {len(transactions)} transactions from platform {dup_platform.id} to {primary_platform.id}")
                    
                    for transaction in transactions:
                        transaction.platform_id = primary_platform.id
                        transaction_updates += 1
                    
                    # Update holdings (with conflict resolution)
                    holdings = Holding.query.filter_by(platform_id=dup_platform.id).all()
                    print(f"  Moving {len(holdings)} holdings from platform {dup_platform.id} to {primary_platform.id}")
                    
                    for holding in holdings:
                        # Check if a holding already exists for this platform+security combination
                        existing_holding = Holding.query.filter_by(
                            platform_id=primary_platform.id, 
                            security_id=holding.security_id
                        ).first()
                        
                        if existing_holding:
                            # Merge the holdings by adding quantities and values
                            print(f"    Merging holding for security {holding.security_id}: {existing_holding.quantity} + {holding.quantity}")
                            existing_holding.quantity += holding.quantity
                            existing_holding.current_value += holding.current_value
                            existing_holding.total_cost += holding.total_cost
                            # Delete the duplicate holding
                            db.session.delete(holding)
                        else:
                            # No conflict, just update the platform_id
                            holding.platform_id = primary_platform.id
                            holdings_updates += 1
                    
                    # Commit updates before deleting
                    db.session.commit()
                    
                    # Now safe to delete the duplicate platform
                    db.session.delete(dup_platform)
                    consolidation_count += 1
        
        # Final commit
        try:
            db.session.commit()
            print(f"\n=== Cleanup Summary ===")
            print(f"Platforms consolidated: {consolidation_count}")
            print(f"Transactions updated: {transaction_updates}")
            print(f"Holdings updated: {holdings_updates}")
            print(f"Final platform count: {len(all_platforms) - consolidation_count}")
            
            # Show final platform list
            remaining_platforms = Platform.query.all()
            print(f"\nRemaining platforms ({len(remaining_platforms)}):")
            for platform in remaining_platforms:
                transaction_count = Transaction.query.filter_by(platform_id=platform.id).count()
                holdings_count = Holding.query.filter_by(platform_id=platform.id).count()
                account_display = platform.account_type if platform.account_type else "None"
                print(f"  {platform.id}: {platform.name}_{account_display} ({transaction_count} transactions, {holdings_count} holdings)")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error during cleanup: {e}")
            return False
            
        return True

if __name__ == "__main__":
    success = safe_cleanup_platforms()
    if success:
        print("\n✅ Safe platform cleanup completed successfully!")
    else:
        print("\n❌ Safe platform cleanup failed!")
        sys.exit(1)