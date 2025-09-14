# Git Commands to Push Safe Scripts to Pi

## Step 1: Add and commit the new safe scripts
```bash
# On Windows (in your project directory)
git add backend/safe_cleanup_platforms.py
git add backend/safe_fix_securities.py  
git add backend/check_holdings_integrity.py
git commit -m "Add safe cleanup scripts that handle holdings table properly"
git push origin main
```

## Step 2: On Pi, pull the latest changes
```bash
# On Pi
cd ~/investment-tracker
git pull origin main
```

## Step 3: Verify files are available in Docker
```bash
# On Pi - check if files are now in the container
docker-compose exec backend ls -la /app/ | grep safe
docker-compose exec backend ls -la /app/ | grep check_holdings
```

## Step 4: Run the safe cleanup sequence
```bash
# On Pi - run in this exact order:

# 1. Check current holdings integrity issues
docker-compose exec backend python /app/check_holdings_integrity.py

# 2. Run safe platform cleanup (114 → ~5 platforms)
docker-compose exec backend python /app/safe_cleanup_platforms.py

# 3. Run safe security cleanup (fix exchange/currency issues)
docker-compose exec backend python /app/safe_fix_securities.py

# 4. Verify final results
docker-compose exec backend python -c "
from app import create_app, db
from app.models.platform import Platform
from app.models.security import Security
from app.models.transaction import Transaction

app = create_app()
with app.app_context():
    print('=== FINAL RESULTS ===')
    print(f'Platforms: {Platform.query.count()}')
    print(f'Securities: {Security.query.count()}')
    print(f'Transactions: {Transaction.query.count()}')
"

# 5. Final platform status check
docker-compose exec backend python /app/check_platform_status.py
```

## Expected Results:
- **Before**: 114 platforms → **After**: ~5 platforms
- **Before**: UK stocks marked as NASDAQ → **After**: Correctly marked as LSE
- **Before**: Duplicate securities → **After**: Consolidated
- **Before**: Holdings constraint violations → **After**: All resolved

The safe scripts handle the holdings table properly, so no more constraint violations should occur.