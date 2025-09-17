"""
Small CSV validator to find rows that fail Decimal parsing and rows that attempt to sell
more shares than held (basic simulation).

Run inside the backend container:
 docker-compose exec backend python validate_csv.py
"""
import argparse
import pandas as pd
from decimal import Decimal, InvalidOperation
import os
from typing import List, Dict, Any


CSV_PATH = '/app/data/combined_transactions_updated.csv'


def _normalize_numeric_str(s: str) -> str:
    """Normalize numeric-looking strings: remove currency symbols, handle European decimals,
    parentheses negatives, and strip non-numeric characters."""
    if s is None:
        return None
    s = str(s).strip()
    if s == '':
        return None
    for ch in ['\u00a3', '$', '\u20ac', '\u00a5', '\xa0']:
        s = s.replace(ch, '')
    s = s.replace(' ', '')
    if s.startswith('(') and s.endswith(')'):
        s = '-' + s[1:-1]
    # European style: 1.234,56 -> 1234.56
    if s.count(',') == 1 and s.count('.') >= 1 and s.rfind('.') < s.rfind(','):
        s = s.replace('.', '').replace(',', '.')
    else:
        if ',' in s and '.' not in s:
            s = s.replace(',', '.')
        else:
            s = s.replace(',', '')
    allowed = set('0123456789.-')
    s = ''.join(ch for ch in s if ch in allowed)
    if s in ['', '-', '.']:
        return None
    return s


def parse_decimal(val):
    try:
        s = _normalize_numeric_str(val)
        if s is None:
            return None
        return Decimal(s)
    except (InvalidOperation, TypeError):
        return None


def _last_buy_rows(df: pd.DataFrame, ticker: str, upto_idx: int, n: int = 3) -> pd.DataFrame:
    """Return last n BUY rows for ticker up to (but not including) index upto_idx."""
    mask = (df.index < upto_idx) & (df['ticker'].fillna('').str.strip().str.upper() == ticker.upper()) & (
        df['type'].fillna('').str.strip().str.upper() == 'BUY')
    return df.loc[mask].tail(n)


def find_issues(csv_path: str = CSV_PATH, write_report: bool = False, write_fixed: bool = False) -> Dict[str, Any]:
    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}")
        return {}

    df = pd.read_csv(csv_path, dtype=str)
    df.columns = df.columns.str.strip().str.lower()

    decimal_errors: List[int] = []
    sell_too_many: List[int] = []
    decimal_error_rows: List[Dict[str, Any]] = []
    sell_error_rows: List[Dict[str, Any]] = []

    holdings: Dict[str, Decimal] = {}

    # iterate in file order (import_data sorts by date; validator should reflect raw ordering)
    for idx, row in df.iterrows():
        ticker = str(row.get('ticker')).strip() if row.get('ticker') else ''
        transaction_type = str(row.get('type')).strip().upper() if row.get('type') else ''

        qty = parse_decimal(row.get('quantity'))
        price = parse_decimal(row.get('price_per_share'))
        total = parse_decimal(row.get('total_amount'))

        if qty is None or price is None or total is None:
            decimal_errors.append(idx)
            decimal_error_rows.append({'index': idx, 'row': row.to_dict(), 'quantity': row.get('quantity'),
                                       'price_per_share': row.get('price_per_share'), 'total_amount': row.get('total_amount')})

        if ticker:
            holdings.setdefault(ticker.upper(), Decimal('0'))
            if transaction_type == 'BUY':
                if qty is not None:
                    holdings[ticker.upper()] += qty
            elif transaction_type == 'SELL':
                if qty is None:
                    # already counted as decimal error
                    pass
                else:
                    if holdings[ticker.upper()] - qty < 0:
                        sell_too_many.append(idx)
                        # capture context: holdings before sell and last buy rows
                        before = holdings[ticker.upper()]
                        buys = _last_buy_rows(df, ticker, idx, n=5).to_dict(orient='records')
                        sell_error_rows.append({'index': idx, 'row': row.to_dict(), 'holdings_before': str(before), 'last_buys': buys})
                    else:
                        holdings[ticker.upper()] -= qty

    print(f"Decimal parse errors in rows: {decimal_errors}")
    print(f"Rows attempting to sell more shares than held: {sell_too_many}")

    if decimal_error_rows:
        print('\nSample decimal error rows (first 20):')
        for item in decimal_error_rows[:20]:
            print(f"Row {item['index']}: quantity={item['quantity']} price_per_share={item['price_per_share']} total_amount={item['total_amount']}")

    if sell_error_rows:
        print('\nSample sell-too-many rows (first 20) with context:')
        for item in sell_error_rows[:20]:
            print(f"Row {item['index']}: holdings_before={item['holdings_before']} ticker={item['row'].get('ticker')} type={item['row'].get('type')} quantity={item['row'].get('quantity')}")
            if item['last_buys']:
                print('  Last buy rows (up to 5):')
                for b in item['last_buys']:
                    # print minimal buy context
                    print(f"    date={b.get('timestamp')} ticker={b.get('ticker')} quantity={b.get('quantity')} total_amount={b.get('total_amount')}")
            else:
                print('  No prior buys found for this ticker in the file')

    report = {'decimal_errors': decimal_errors, 'sell_too_many': sell_too_many}

    if write_report:
        report_path = os.path.join(os.path.dirname(csv_path), 'validation_report.csv')
        print(f"Writing report to {report_path}")
        # write combined report with error type
        rows = []
        for d in decimal_error_rows:
            r = d['row']
            r['_error'] = 'decimal'
            r['_index'] = d['index']
            rows.append(r)
        for s in sell_error_rows:
            r = s['row']
            r['_error'] = 'sell_too_many'
            r['_index'] = s['index']
            r['_holdings_before'] = s['holdings_before']
            rows.append(r)
        rep_df = pd.DataFrame(rows)
        rep_df.to_csv(report_path, index=False)
        print(f"Report written: {report_path}")

    if write_fixed:
        fixed_path = os.path.join(os.path.dirname(csv_path), 'combined_transactions_updated.fixed.csv')
        print(f"Writing normalized CSV to {fixed_path}")
        fixed_df = df.copy()
        for col in ['quantity', 'price_per_share', 'total_amount', 'fx_rate']:
            if col in fixed_df.columns:
                fixed_df[col] = fixed_df[col].apply(lambda v: _normalize_numeric_str(v) if pd.notna(v) else v)
        fixed_df.to_csv(fixed_path, index=False)
        print(f"Fixed CSV written: {fixed_path}")

    return report


def main():
    parser = argparse.ArgumentParser(description='Validate transaction CSV and optionally write fixes')
    parser.add_argument('--csv', help='Path to CSV file', default=CSV_PATH)
    parser.add_argument('--report', action='store_true', help='Write a CSV report of problematic rows')
    parser.add_argument('--write-fixed', action='store_true', help='Write a normalized CSV to disk')
    args = parser.parse_args()

    find_issues(csv_path=args.csv, write_report=args.report, write_fixed=args.write_fixed)


if __name__ == '__main__':
    main()
