#!/bin/bash
# AST Viewer Production Entrypoint Script

set -e

echo "🚀 Starting AST Viewer Code Intelligence Platform..."

# Wait for database connections
echo "⏳ Waiting for Neo4j..."
while ! nc -z ${NEO4J_HOST:-neo4j} ${NEO4J_PORT:-7687}; do
    sleep 2
    echo "   ... still waiting for Neo4j"
done
echo "✅ Neo4j is ready"

echo "⏳ Waiting for Redis..."
while ! nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}; do
    sleep 2
    echo "   ... still waiting for Redis"
done
echo "✅ Redis is ready"

# Optional PostgreSQL check
if [ "${POSTGRES_ENABLED:-false}" = "true" ]; then
    echo "⏳ Waiting for PostgreSQL..."
    while ! nc -z ${POSTGRES_HOST:-postgres} ${POSTGRES_PORT:-5432}; do
        sleep 2
        echo "   ... still waiting for PostgreSQL"
    done
    echo "✅ PostgreSQL is ready"
fi

# Run database migrations/setup if needed
echo "🔧 Setting up database schema..."
python -c "
import asyncio
from src.ast_viewer.database.setup import setup_database
asyncio.run(setup_database())
print('✅ Database setup complete')
"

# Pre-load any required data or models
echo "📚 Pre-loading models and data..."
python -c "
from src.ast_viewer.analyzers.universal import UniversalAnalyzer
from src.ast_viewer.visualizations.engine import VisualizationEngine
analyzer = UniversalAnalyzer()
viz_engine = VisualizationEngine()
print(f'✅ Loaded {len(analyzer.get_supported_languages())} language analyzers')
print(f'✅ Loaded {len(viz_engine.get_available_visualizations())} visualization types')
"

# Start the application with gunicorn for production
echo "🎯 Starting AST Viewer API server..."

exec /opt/venv/bin/gunicorn \
    --bind 0.0.0.0:8000 \
    --workers ${MAX_WORKERS:-4} \
    --worker-class uvicorn.workers.UvicornWorker \
    --worker-timeout ${WORKER_TIMEOUT:-300} \
    --keep-alive ${KEEP_ALIVE:-2} \
    --max-requests ${MAX_REQUESTS:-1000} \
    --max-requests-jitter ${MAX_REQUESTS_JITTER:-100} \
    --preload \
    --log-level ${LOG_LEVEL:-info} \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --enable-stdio-inheritance \
    src.ast_viewer.api.main:app
