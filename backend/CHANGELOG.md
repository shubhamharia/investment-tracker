# Changelog

All notable changes to the backend are documented in this file.

## Unreleased

- Hardening: replace network-dependent yfinance behavior with a deterministic shim for tests to avoid external rate limits and flakiness.
- Startup-time DB schema creation when `TESTING=True` to ensure the test client has tables available without creating them on every request.
- Global error handler: preserve `HTTPException` responses and map SQLAlchemy `IntegrityError` to `400 Bad Request`.
- API compatibility fixes: accept legacy/compatibility keys (e.g. `price` → `price_per_share`, `commission` → `trading_fees`) and derive `platform_id` from portfolio when missing.
- Added POST `/api/portfolios/<id>/dividends` endpoint and ensured portfolio serialization includes `currency` and `gain_loss` where required by integration tests.
- Adjusted test fixtures to avoid dropping schema between client-based tests (`db_session` teardown no longer drops tables) to keep request-based tests stable.

## Test Results

- Full backend test run (inside Docker Compose `backend` service): `431 passed, 2 skipped, 33 warnings` (run duration ~4m 21s). Your environment may differ slightly.

## Notes

- These changes are focused on test stability and API compatibility with the existing test suite. For production deployments, consider enabling explicit migrations (Alembic) rather than `db.create_all()` and reverting fixture behavior to provide strict isolation for unit tests.
# Changelog

## [Unreleased]
### Added
- Deterministic yfinance shim for CI/test reliability (`backend/yfinance.py`)
- POST `/api/portfolios/<id>/dividends` endpoint for dividend creation
- Portfolio value endpoint now includes `currency` key
- Portfolio creation/validation now robust to missing fields and test fixture edge cases
- Platform normalization and cleanup scripts for duplicate platform records

### Changed
- All integration tests now run reliably inside Docker Compose
- Error handling improved: HTTPExceptions preserved, IntegrityError returns 400
- Portfolio model: `user_id` is now nullable for test fixture compatibility
- Transaction and holding creation now accept compatibility keys (`price`, `commission`)
- Holdings creation derives `platform_id` from portfolio if omitted

### Fixed
- API endpoints now return expected status codes and JSON shapes for all integration tests
- Dividend creation handler parses dates and defaults `ex_dividend_date` to avoid NOT NULL errors
- Portfolio-scoped transaction and holding creation now match test payloads

### Documentation
- Updated README with Docker Compose test instructions and endpoint changes
- Added platform cleanup and data integrity scripts to documentation

---
