#!/usr/bin/env python3
"""
Security data verification script to identify and fix data quality issues
"""
import sys
import os
sys.path.append('/app')

from app import create_app, db
from app.models.security import Security
from app.models.transaction import Transaction

def verify_securities():
    """Verify and report on security data quality issues"""
    app = create_app()
    
    with app.app_context():
        print("=== Security Data Verification ===")
        
        securities = Security.query.all()
        print(f"Total securities: {len(securities)}")
        
        print("\n=== Issue Analysis ===")
        
        # Issue 1: UK stocks marked as NASDAQ
        uk_nasdaq_securities = Security.query.filter(
            Security.isin.like('GB%'),
            Security.exchange == 'NASDAQ'
        ).all()
        
        print(f"1. UK stocks incorrectly marked as NASDAQ: {len(uk_nasdaq_securities)}")
        for sec in uk_nasdaq_securities[:5]:  # Show first 5
            print(f"   - {sec.ticker} (ISIN: {sec.isin}, Currency: {sec.currency})")
        if len(uk_nasdaq_securities) > 5:
            print(f"   ... and {len(uk_nasdaq_securities) - 5} more")
        
        # Issue 2: Currency mismatches for UK stocks
        uk_usd_securities = Security.query.filter(
            Security.isin.like('GB%'),
            Security.currency == 'USD'
        ).all()
        
        print(f"\n2. UK stocks with USD currency: {len(uk_usd_securities)}")
        for sec in uk_usd_securities[:5]:
            print(f"   - {sec.ticker} (ISIN: {sec.isin}, Exchange: {sec.exchange})")
        
        # Issue 3: Duplicate securities by ISIN
        print(f"\n3. Checking for duplicate securities by ISIN...")
        isin_groups = {}
        for sec in securities:
            if sec.isin:
                if sec.isin not in isin_groups:
                    isin_groups[sec.isin] = []
                isin_groups[sec.isin].append(sec)
        
        duplicates = {isin: secs for isin, secs in isin_groups.items() if len(secs) > 1}
        print(f"   ISINs with multiple securities: {len(duplicates)}")
        
        for isin, secs in list(duplicates.items())[:3]:  # Show first 3
            print(f"   - {isin}:")
            for sec in secs:
                tx_count = Transaction.query.filter_by(security_id=sec.id).count()
                print(f"     * {sec.ticker} ({sec.exchange}, {sec.currency}) - {tx_count} transactions")
        
        # Issue 4: Missing names
        no_name_count = Security.query.filter(Security.name.is_(None)).count()
        print(f"\n4. Securities without names: {no_name_count}")
        
        # Issue 5: Check some specific problematic cases
        print(f"\n5. Specific problem cases:")
        
        # Check HSBA examples
        hsba_securities = Security.query.filter(Security.ticker.like('HSBA%')).all()
        print(f"   HSBA variations: {len(hsba_securities)}")
        for sec in hsba_securities:
            tx_count = Transaction.query.filter_by(security_id=sec.id).count()
            print(f"   - {sec.ticker}: {sec.exchange}, {sec.currency} ({tx_count} transactions)")

if __name__ == "__main__":
    verify_securities()