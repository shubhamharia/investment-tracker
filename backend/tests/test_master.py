import pytest
import pandas as pd
from app import create_app, db
from app.models import Platform, Security, Transaction, Holding, Dividend, PriceHistory
from datetime import datetime
import os

class TestMasterIntegration:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_platform_import(self):
        """Test importing platforms from CSV"""
        df = pd.read_csv('tests/test_data/platforms.csv')
        errors = []
        
        for _, row in df.iterrows():
            platform = Platform(
                name=row['name'],
                description=row['description']
            )
            try:
                db.session.add(platform)
                db.session.commit()
            except Exception as e:
                errors.append(f"Error importing platform {row['name']}: {str(e)}")
                db.session.rollback()

        assert len(errors) == 0, f"Platform import errors: {errors}"

    def test_security_import(self):
        """Test importing securities from CSV"""
        df = pd.read_csv('tests/test_data/securities.csv')
        errors = []
        
        for _, row in df.iterrows():
            security = Security(
                symbol=row['symbol'],
                name=row['name'],
                security_type=row['security_type']
            )
            try:
                db.session.add(security)
                db.session.commit()
            except Exception as e:
                errors.append(f"Error importing security {row['symbol']}: {str(e)}")
                db.session.rollback()

        assert len(errors) == 0, f"Security import errors: {errors}"

    def test_transaction_import(self):
        """Test importing transactions from CSV"""
        df = pd.read_csv('tests/test_data/transactions.csv')
        errors = []
        
        for _, row in df.iterrows():
            transaction = Transaction(
                security_id=row['security_id'],
                platform_id=row['platform_id'],
                transaction_type=row['transaction_type'],
                quantity=row['quantity'],
                price=row['price'],
                date=datetime.strptime(row['date'], '%Y-%m-%d'),
                fees=row.get('fees', 0)
            )
            try:
                db.session.add(transaction)
                db.session.commit()
                
                # Validate transaction data
                self._validate_transaction(transaction)
                
            except Exception as e:
                errors.append(f"Error importing transaction {row}: {str(e)}")
                db.session.rollback()

        assert len(errors) == 0, f"Transaction import errors: {errors}"

    def _validate_transaction(self, transaction):
        """Validate transaction data"""
        errors = []
        
        # Check if security exists
        if not Security.query.get(transaction.security_id):
            errors.append(f"Security ID {transaction.security_id} not found")
        
        # Check if platform exists
        if not Platform.query.get(transaction.platform_id):
            errors.append(f"Platform ID {transaction.platform_id} not found")
        
        # Validate quantity and price
        if transaction.quantity <= 0:
            errors.append(f"Invalid quantity: {transaction.quantity}")
        if transaction.price <= 0:
            errors.append(f"Invalid price: {transaction.price}")

        assert len(errors) == 0, f"Transaction validation errors: {errors}"

    def test_holdings_calculation(self):
        """Test if holdings are calculated correctly"""
        holdings = Holding.query.all()
        errors = []
        
        for holding in holdings:
            # Calculate expected holding from transactions
            transactions = Transaction.query.filter_by(
                security_id=holding.security_id,
                platform_id=holding.platform_id
            ).all()
            
            expected_quantity = sum(
                t.quantity if t.transaction_type == 'BUY' else -t.quantity 
                for t in transactions
            )
            
            if abs(holding.quantity - expected_quantity) > 0.0001:
                errors.append(
                    f"Holding mismatch for security {holding.security_id}: "
                    f"Expected {expected_quantity}, got {holding.quantity}"
                )

        assert len(errors) == 0, f"Holdings calculation errors: {errors}"

    def test_dividend_import(self):
        """Test importing dividends from CSV"""
        df = pd.read_csv('tests/test_data/dividends.csv')
        errors = []
        
        for _, row in df.iterrows():
            dividend = Dividend(
                security_id=row['security_id'],
                platform_id=row['platform_id'],
                amount=row['amount'],
                date=datetime.strptime(row['date'], '%Y-%m-%d')
            )
            try:
                db.session.add(dividend)
                db.session.commit()
            except Exception as e:
                errors.append(f"Error importing dividend {row}: {str(e)}")
                db.session.rollback()

        assert len(errors) == 0, f"Dividend import errors: {errors}"

    def test_price_history(self):
        """Test price history data"""
        securities = Security.query.all()
        errors = []
        
        for security in securities:
            prices = PriceHistory.query.filter_by(security_id=security.id).all()
            
            if not prices:
                errors.append(f"No price history for security {security.symbol}")
                continue
            
            # Check for price continuity
            for i in range(1, len(prices)):
                price_diff = abs(prices[i].price - prices[i-1].price) / prices[i-1].price
                if price_diff > 0.2:  # Flag suspicious price movements (>20%)
                    errors.append(
                        f"Suspicious price movement for {security.symbol}: "
                        f"{prices[i-1].date}: {prices[i-1].price} -> "
                        f"{prices[i].date}: {prices[i].price}"
                    )

        assert len(errors) == 0, f"Price history errors: {errors}"

if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])