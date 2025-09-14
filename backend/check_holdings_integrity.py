#!/usr/bin/env python3
"""
Check holdings table for NULL foreign key issues
"""
import sys
import os
sys.path.append('/app')

from app import create_app, db
from app.models.platform import Platform
from app.models.security import Security
from app.models.transaction import Transaction
from app.models.holding import Holding

def check_holdings_integrity():
    """Check for holdings with NULL foreign keys"""
    app = create_app()
    
    with app.app_context():
        print("=== Holdings Integrity Check ===")
        
        # Check total counts
        platforms = Platform.query.count()
        securities = Security.query.count()
        transactions = Transaction.query.count()
        holdings = Holding.query.count()
        
        print(f"Database counts:")
        print(f"  Platforms: {platforms}")
        print(f"  Securities: {securities}")
        print(f"  Transactions: {transactions}")
        print(f"  Holdings: {holdings}")
        
        # Check for NULL platform_id in holdings
        null_platform_holdings = Holding.query.filter(Holding.platform_id.is_(None)).all()
        print(f"\nHoldings with NULL platform_id: {len(null_platform_holdings)}")
        
        if null_platform_holdings:
            print("Sample holdings with NULL platform_id:")
            for holding in null_platform_holdings[:5]:
                print(f"  Holding ID {holding.id}: portfolio_id={holding.portfolio_id}, security_id={holding.security_id}")
        
        # Check for NULL security_id in holdings  
        null_security_holdings = Holding.query.filter(Holding.security_id.is_(None)).all()
        print(f"\nHoldings with NULL security_id: {len(null_security_holdings)}")
        
        if null_security_holdings:
            print("Sample holdings with NULL security_id:")
            for holding in null_security_holdings[:5]:
                print(f"  Holding ID {holding.id}: portfolio_id={holding.portfolio_id}, platform_id={holding.platform_id}")
        
        # Check for invalid foreign key references
        print(f"\nChecking foreign key integrity...")
        
        # Holdings referencing non-existent platforms
        invalid_platform_holdings = db.session.query(Holding).filter(
            ~Holding.platform_id.in_(db.session.query(Platform.id))
        ).all()
        print(f"Holdings referencing non-existent platforms: {len(invalid_platform_holdings)}")
        
        # Holdings referencing non-existent securities
        invalid_security_holdings = db.session.query(Holding).filter(
            ~Holding.security_id.in_(db.session.query(Security.id))
        ).all()
        print(f"Holdings referencing non-existent securities: {len(invalid_security_holdings)}")
        
        # Show platform distribution
        print(f"\nPlatform distribution:")
        platform_counts = db.session.query(
            Platform.name, 
            Platform.account_type,
            db.func.count(Holding.id).label('holdings_count'),
            db.func.count(Transaction.id).label('transactions_count')
        ).outerjoin(Holding).outerjoin(Transaction).group_by(Platform.id, Platform.name, Platform.account_type).all()
        
        for name, account_type, holdings_count, tx_count in platform_counts[:10]:
            account_display = account_type if account_type else "None"
            print(f"  {name}_{account_display}: {tx_count} transactions, {holdings_count} holdings")
        
        if len(platform_counts) > 10:
            print(f"  ... and {len(platform_counts) - 10} more platforms")

if __name__ == "__main__":
    check_holdings_integrity()