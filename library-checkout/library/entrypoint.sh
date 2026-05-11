#!/bin/sh
set -e

echo "============================================"
echo "  Running unit tests (SQLite in-memory)..."
echo "============================================"
pytest tests/ -v --tb=short

echo "============================================"
echo "  All tests passed. Starting application..."
echo "  ENV: ${APP_ENV:-production}"
echo "  LOG_LEVEL: ${LOG_LEVEL:-info}"
echo "============================================"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level "${LOG_LEVEL:-info}"
