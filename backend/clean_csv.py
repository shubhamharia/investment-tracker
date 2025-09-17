"""
CSV cleaner to fix common formatting issues that cause Decimal parsing errors.

Usage (inside project root):
  docker-compose exec backend python clean_csv.py --dry-run
  docker-compose exec backend python clean_csv.py

Output:
  - Writes cleaned CSV to /app/data/combined_transactions_updated.cleaned.csv
  - Prints rows that still fail numeric parsing for manual inspection
"""
import pandas as pd
import os
import argparse
from decimal import Decimal, InvalidOperation

CSV_IN = '/app/data/combined_transactions_updated.csv'
CSV_OUT = '/app/data/combined_transactions_updated.cleaned.csv'
NUMERIC_COLS = ['total_amount', 'quantity', 'price_per_share', 'fx_rate']


def normalize_str(s):
    if pd.isna(s):
        return s
    t = str(s).strip()
    if t == '':
        return None

    # Common currency symbols
    for ch in ['£', '$', '€', '¥']:
        t = t.replace(ch, '')

    # Remove non-breaking spaces and regular spaces
    t = t.replace('\xa0', '').replace(' ', '')

    # Replace parentheses used for negative numbers (e.g. (1,234.56))
    if t.startswith('(') and t.endswith(')'):
        t = '-' + t[1:-1]

    # If number uses comma as decimal separator and dot as thousands sep like '1.234,56'
    if t.count(',') == 1 and t.count('.') >= 1 and t.rfind('.') < t.rfind(','):
        # remove dots (thousands) and replace comma with dot
        t = t.replace('.', '').replace(',', '.')
    else:
        # remove thousands separator commas
        # but if it contains comma and no dot, it might be decimal comma - convert
        if ',' in t and '.' not in t:
            # assume comma is decimal separator
            t = t.replace(',', '.')
        else:
            t = t.replace(',', '')

    # Strip any lingering non-numeric characters
    allowed = set('0123456789.-')
    cleaned = ''.join(ch for ch in t if ch in allowed)
    if cleaned == '':
        return None
    return cleaned


def try_decimal(val):
    if val is None:
        return None
    try:
        return Decimal(str(val))
    except InvalidOperation:
        return None


def clean_csv(dry_run=True):
    if not os.path.exists(CSV_IN):
        print(f"Input CSV not found: {CSV_IN}")
        return 1

    df = pd.read_csv(CSV_IN, dtype=str)
    df.columns = df.columns.str.strip().str.lower()

    invalid_rows = set()

    for col in NUMERIC_COLS:
        if col not in df.columns:
            continue
        cleaned_vals = []
        for idx, v in df[col].items():
            norm = normalize_str(v)
            dec = try_decimal(norm)
            if dec is None and (norm is not None and norm != ''):
                invalid_rows.add(idx)
            cleaned_vals.append(norm)
        df[col] = cleaned_vals

    print(f"Found {len(invalid_rows)} rows with remaining numeric parse issues")
    if len(invalid_rows) > 0:
        print("Sample problematic rows:")
        print(df.loc[sorted(list(invalid_rows))].head(20).to_string())

    if dry_run:
        print(f"Dry-run: cleaned CSV not written. To write, re-run without --dry-run")
        return 0

    # Write cleaned CSV
    df.to_csv(CSV_OUT, index=False)
    print(f"Cleaned CSV written to: {CSV_OUT}")
    print("Please review the sample problematic rows above and fix them manually if needed.")
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Do not write cleaned CSV')
    args = parser.parse_args()
    clean_csv(dry_run=args.dry_run)
