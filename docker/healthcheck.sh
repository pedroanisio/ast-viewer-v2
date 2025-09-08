#!/bin/bash
# AST Viewer Health Check Script

set -e

# Check if the main API is responding
if ! curl -f -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "❌ API health check failed"
    exit 1
fi

# Check database connectivity
if ! python -c "
import os
try:
    from src.ast_viewer.database.connection import check_neo4j_connection
    if check_neo4j_connection():
        print('✅ Neo4j connection healthy')
    else:
        print('❌ Neo4j connection failed')
        exit(1)
except Exception as e:
    print(f'❌ Database check error: {e}')
    exit(1)
" 2>/dev/null; then
    echo "❌ Database health check failed"
    exit 1
fi

# Check Redis connectivity
if ! python -c "
import redis
import os
try:
    r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
    r.ping()
    print('✅ Redis connection healthy')
except Exception as e:
    print(f'❌ Redis check error: {e}')
    exit(1)
" 2>/dev/null; then
    echo "❌ Redis health check failed"
    exit 1
fi

echo "✅ All health checks passed"
exit 0
