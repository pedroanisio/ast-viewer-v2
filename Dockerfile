# AST Viewer Code Intelligence Platform - Multi-stage Docker Build
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_SYSTEM_PYTHON=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Essential build tools
    build-essential \
    curl \
    git \
    # Tree-sitter requirements
    pkg-config \
    # Visualization dependencies
    graphviz \
    graphviz-dev \
    # Image processing
    libpng-dev \
    libjpeg-dev \
    # Neo4j driver dependencies
    libssl-dev \
    libffi-dev \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv for fast Python package management
RUN pip install uv

# Create app user for security
RUN groupadd -r astviewer && useradd -r -g astviewer astviewer

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./
COPY README.md ./

# Development stage
FROM base AS development

# Install development dependencies
RUN uv sync --dev --frozen

# Copy source code
COPY src/ ./src/
# Create tests directory (will be mounted in development)
RUN mkdir -p ./tests

# Set up development environment
ENV DEBUG=true \
    LOG_LEVEL=DEBUG \
    PYTHONPATH=/app/src

# Create directories
RUN mkdir -p /app/temp /app/exports /app/dev-data && \
    chown -R astviewer:astviewer /app

# Switch to app user
USER astviewer

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default development command
CMD ["uvicorn", "src.ast_viewer.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production build stage
FROM base AS builder

# Install production dependencies and create virtual environment
RUN uv sync --frozen --no-dev

# Create a virtual environment and copy the installed packages
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install all dependencies including gunicorn into the virtual environment
RUN /opt/venv/bin/pip install --no-cache-dir \
    gunicorn>=23.0.0 \
    uvicorn>=0.32.1 \
    fastapi>=0.115.0 \
    pydantic>=2.11.7 \
    neo4j>=5.28.2 \
    redis>=6.4.0 \
    sqlalchemy>=2.0.43 \
    psycopg2-binary>=2.9.10 \
    asyncpg>=0.30.0 \
    alembic>=1.16.5 \
    strawberry-graphql>=0.282.0 \
    matplotlib>=3.10.6 \
    plotly>=6.3.0 \
    seaborn>=0.13.2 \
    networkx>=3.5 \
    tree-sitter>=0.25.1 \
    tree-sitter-python>=0.23.6 \
    tree-sitter-javascript>=0.25.0 \
    tree-sitter-typescript>=0.23.2 \
    tree-sitter-go>=0.25.0 \
    tree-sitter-rust>=0.24.0

# Copy source code
COPY src/ ./src/

# Build optimizations
RUN python -m compileall src/ && \
    find . -name "*.pyc" -delete && \
    find . -name "__pycache__" -type d -exec rm -rf {} + || true

# Production stage
FROM python:3.11-slim AS production

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBUG=false \
    LOG_LEVEL=INFO \
    PYTHONPATH=/app/src \
    PATH=/opt/venv/bin:$PATH \
    MPLCONFIGDIR=/tmp/matplotlib

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    # Runtime libraries
    libssl3 \
    libffi8 \
    graphviz \
    libpng16-16 \
    libjpeg62-turbo \
    # Process management
    dumb-init \
    # Monitoring tools
    curl \
    # Network tools
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user
RUN groupadd -r astviewer && useradd -r -g astviewer astviewer

# Set working directory
WORKDIR /app

# Copy Python virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --from=builder --chown=astviewer:astviewer /app/src ./src

# Create necessary directories with proper permissions
RUN mkdir -p /app/temp /app/exports /app/logs && \
    chown -R astviewer:astviewer /app && \
    chmod -R 755 /app

# Copy configuration files
COPY --chown=astviewer:astviewer docker/entrypoint.sh /entrypoint.sh
COPY --chown=astviewer:astviewer docker/healthcheck.sh /healthcheck.sh
RUN chmod +x /entrypoint.sh /healthcheck.sh

# Switch to app user
USER astviewer

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /healthcheck.sh

# Use dumb-init for proper signal handling
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Production command with gunicorn
CMD ["/entrypoint.sh"]

# Add labels for metadata
LABEL \
    org.opencontainers.image.title="AST Viewer Code Intelligence Platform" \
    org.opencontainers.image.description="Enterprise-grade code intelligence platform with multi-language support" \
    org.opencontainers.image.vendor="AST Viewer" \
    org.opencontainers.image.version="2.0.0" \
    org.opencontainers.image.licenses="MIT"
