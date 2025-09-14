#!/usr/bin/env python3
"""
Safe security cleanup script that handles holdings table properly
"""
import sys
import os
sys.path.append('/app')

from app import create_app, db
from app.models.security import Security
from app.models.transaction import Transaction
from app.models.holding import Holding

def safe_fix_securities():
    """Safely fix security data issues handling holdings table"""
    app = create_app()
    
    with app.app_context():
        print("=== SAFE Security Data Cleanup ===")
        
        securities = Security.query.all()
        print(f"Total securities before cleanup: {len(securities)}")
        
        fixes_applied = 0
        
        # Fix 1: Correct UK stocks marked as NASDAQ
        print("\n1. Fixing UK stocks incorrectly marked as NASDAQ...")
        uk_nasdaq_securities = Security.query.filter(
            Security.isin.like('GB%'),
            Security.exchange == 'NASDAQ'
        ).all()
        
        for sec in uk_nasdaq_securities:
            print(f"   Fixing {sec.ticker}: NASDAQ -> LSE")
            sec.exchange = 'LSE'
            sec.country = 'GB'
            fixes_applied += 1
        
        # Fix 2: Correct currency for UK stocks
        print("\n2. Fixing currency for UK stocks...")
        uk_securities = Security.query.filter(Security.isin.like('GB%')).all()
        
        for sec in uk_securities:
            # Determine correct currency based on ticker
            if sec.ticker and sec.ticker.endswith('.L'):
                # LSE stocks should be GBX (pence) for most cases
                if sec.currency != 'GBX':
                    print(f"   Fixing {sec.ticker}: {sec.currency} -> GBX")
                    sec.currency = 'GBX'
                    fixes_applied += 1
            else:
                # Trading212 format UK stocks might be GBP
                if sec.currency == 'USD':
                    print(f"   Fixing {sec.ticker}: USD -> GBP")
                    sec.currency = 'GBP'
                    fixes_applied += 1
        
        # Commit currency/exchange fixes first
        db.session.commit()
        
        # Fix 3: Consolidate duplicate securities (SAFE VERSION)
        print("\n3. Safely consolidating duplicate securities...")
        isin_groups = {}
        for sec in Security.query.all():  # Re-query after commits
            if sec.isin:
                if sec.isin not in isin_groups:
                    isin_groups[sec.isin] = []
                isin_groups[sec.isin].append(sec)
        
        duplicates = {isin: secs for isin, secs in isin_groups.items() if len(secs) > 1}
        consolidated = 0
        
        for isin, secs in duplicates.items():
            if len(secs) > 1:
                print(f"   Safely consolidating ISIN {isin} ({len(secs)} securities)")
                
                # Choose the primary security (prefer LSE over others, then by transaction count)
                primary = None
                for sec in secs:
                    tx_count = Transaction.query.filter_by(security_id=sec.id).count()
                    if primary is None or (sec.exchange == 'LSE' and primary.exchange != 'LSE') or tx_count > Transaction.query.filter_by(security_id=primary.id).count():
                        primary = sec
                
                print(f"     Primary security: {primary.ticker} (ID: {primary.id})")
                
                # Update all references to point to primary security
                for sec in secs:
                    if sec.id != primary.id:
                        # Update transactions
                        transactions = Transaction.query.filter_by(security_id=sec.id).all()
                        print(f"     Moving {len(transactions)} transactions from {sec.ticker} to {primary.ticker}")
                        for tx in transactions:
                            tx.security_id = primary.id
                        
                        # Update holdings (CRITICAL - this was missing!)
                        holdings = Holding.query.filter_by(security_id=sec.id).all()
                        print(f"     Moving {len(holdings)} holdings from {sec.ticker} to {primary.ticker}")
                        for holding in holdings:
                            holding.security_id = primary.id
                        
                        # Commit updates before deleting
                        db.session.commit()
                        
                        # Now safe to delete the duplicate security
                        db.session.delete(sec)
                        consolidated += 1
        
        # Final commit
        try:
            db.session.commit()
            print(f"\n=== Cleanup Summary ===")
            print(f"Security fixes applied: {fixes_applied}")
            print(f"Duplicate securities consolidated: {consolidated}")
            
            # Show final statistics
            remaining_securities = Security.query.all()
            print(f"Final security count: {len(remaining_securities)}")
            
            # Show corrected exchange distribution
            exchange_counts = db.session.query(Security.exchange, db.func.count(Security.id)).group_by(Security.exchange).all()
            print("\nSecurities by exchange:")
            for exchange, count in exchange_counts:
                print(f"  {exchange}: {count}")
            
            # Show currency distribution
            currency_counts = db.session.query(Security.currency, db.func.count(Security.id)).group_by(Security.currency).all()
            print("\nSecurities by currency:")
            for currency, count in currency_counts:
                print(f"  {currency}: {count}")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error during cleanup: {e}")
            return False
            
        return True

if __name__ == "__main__":
    success = safe_fix_securities()
    if success:
        print("\n✅ Safe security cleanup completed successfully!")
    else:
        print("\n❌ Safe security cleanup failed!")
        sys.exit(1)