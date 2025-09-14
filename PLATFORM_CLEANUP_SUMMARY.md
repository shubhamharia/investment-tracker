# Platform Duplication Issue - Analysis & Solution

## Problem Analysis

The system created 114 platform records instead of the expected 7 due to inconsistent platform naming in the CSV data.

### Root Cause
The CSV file contains platform names with inconsistent spacing:
- `Trading 212_ISA` (with space) - 127 transactions
- `Trading212_ISA` (without space) - 35 transactions
- `Trading 212_GIA` (with space) - 107 transactions  
- `Trading212_GIA` (without space) - 4 transactions
- `Freetrade` - 54 transactions
- `AJBELL_LISA` - 4 transactions
- `HL_LISA` - 4 transactions

The original `get_or_create_platform()` function treated each variation as a separate platform, creating duplicate database records.

## Solution Implemented

### 1. Enhanced Platform Normalization (`import_data.py`)
```python
def get_or_create_platform(platform_name):
    """Get or create platform record"""
    # Parse platform name and account type
    if '_' in platform_name:
        name, account_type = platform_name.split('_', 1)
    else:
        name = platform_name
        account_type = None
    
    # Normalize the platform name (remove spaces, standardize case)
    name = name.replace(' ', '').strip()
    
    # Standardize common platform name variations
    name_mappings = {
        'TRADING212': 'Trading212',
        'Trading212': 'Trading212',
        'trading212': 'Trading212',
        'HL': 'HL',
        'AJBELL': 'AJBELL',
        'Freetrade': 'Freetrade',
        'FREETRADE': 'Freetrade'
    }
    
    # Apply name standardization
    name = name_mappings.get(name, name)
```

### 2. Database Cleanup Script (`cleanup_platforms.py`)
Created a script to:
- Identify duplicate platform records
- Consolidate them into single canonical records
- Update all transaction references
- Remove duplicate platform entries

### 3. Platform Status Checker (`check_platform_status.py`)
Created a diagnostic script to:
- Display current platform situation
- Show transaction counts per platform
- Group platforms by normalized names

## Expected Results After Cleanup

After running the cleanup script, the system should have:
- **7 unique platforms** instead of 114
- All transactions properly assigned to consolidated platforms
- Consistent platform naming across the system

### Expected Platform Consolidation:
1. `Trading212_ISA` (162 total transactions: 127 + 35)
2. `Trading212_GIA` (111 total transactions: 107 + 4)
3. `Freetrade` (54 transactions)
4. `AJBELL_LISA` (4 transactions)
5. `HL_LISA` (4 transactions)

## Deployment Steps

1. **Update the import script** on the Pi with the enhanced normalization logic
2. **Run the cleanup script** to consolidate existing duplicate platforms:
   ```bash
   docker-compose exec backend python /app/cleanup_platforms.py
   ```
3. **Verify the cleanup** worked correctly:
   ```bash
   docker-compose exec backend python /app/check_platform_status.py
   ```
4. **Test future imports** to ensure no new duplicates are created

## Prevention

The enhanced normalization logic prevents future platform duplications by:
- Removing spaces from platform names before database operations
- Standardizing case variations
- Using a mapping dictionary for known platform variations

This ensures that `Trading 212_ISA` and `Trading212_ISA` are treated as the same platform (`Trading212_ISA`).