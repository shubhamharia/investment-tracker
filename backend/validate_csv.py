"""
Small CSV validator to find rows that fail Decimal parsing and rows that attempt to sell
more shares than held (basic simulation).

Run inside the backend container:
 docker-compose exec backend python validate_csv.py
"""
import pandas as pd
from decimal import Decimal, InvalidOperation
import os

CSV_PATH = '/app/data/combined_transactions_updated.csv'


def parse_decimal(val):
    try:
        return Decimal(str(val))
    except InvalidOperation:
        return None


def find_issues(csv_path=CSV_PATH):
    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip().str.lower()

    decimal_errors = []
    sell_too_many = []

    holdings = {}

    for idx, row in df.iterrows():
        qty = parse_decimal(row.get('quantity'))
        price = parse_decimal(row.get('price_per_share'))
        total = parse_decimal(row.get('total_amount'))

        if qty is None or price is None or total is None:
            decimal_errors.append(idx)

        # Basic holdings simulation grouped by ticker
        ticker = str(row.get('ticker')).strip() if row.get('ticker') else None
        transaction_type = str(row.get('type')).upper() if row.get('type') else None

        if ticker and transaction_type:
            holdings.setdefault(ticker, Decimal('0'))
            if transaction_type == 'BUY':
                if qty is not None:
                    holdings[ticker] += qty
            elif transaction_type == 'SELL':
                if qty is not None:
                    if holdings[ticker] - qty < 0:
                        sell_too_many.append(idx)
                    else:
                        holdings[ticker] -= qty

    print(f"Decimal parse errors in rows: {decimal_errors}")
    print(f"Rows attempting to sell more shares than held: {sell_too_many}")

    # Print sample of problematic rows for quick debugging
    if decimal_errors:
        print('\nSample decimal error rows:')
        print(df.loc[decimal_errors].head(20).to_string())

    if sell_too_many:
        print('\nSample sell-too-many rows:')
        print(df.loc[sell_too_many].head(20).to_string())


if __name__ == '__main__':
    find_issues()
