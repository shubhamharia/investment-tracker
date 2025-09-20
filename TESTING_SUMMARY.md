# Backend Testing Summary

This project includes a comprehensive backend test suite. The tests are executed inside the `backend` Docker service to ensure a reproducible environment with the correct Python dependencies.

How I ran the tests locally in this workspace:

```bash
cd /home/pi/investment-tracker
docker-compose run --rm --entrypoint "" backend sh -c "cd /app && pytest -q"
```

Results from the run performed while hardening the backend:

- `431 passed, 2 skipped, 33 warnings` (run duration ~4m 21s)

Notes and caveats:
- The test suite may emit `PytestReturnNotNoneWarning` warnings for tests that `return True` instead of `assert True` — these are warnings and not failures.
- The project currently uses `db.create_all()` in test startup for convenience; consider converting to Alembic migrations and stricter fixture isolation for production workflows.
