# 🧠 AST Viewer Code Intelligence Platform

A sophisticated soloprenour code intelligence platform with multi-language support and advanced visualizations.

## 🚀 Features

- **Multi-Language Analysis**: Python, JavaScript, TypeScript, Go, Rust
- **Advanced Visualizations**: 17 different visualization types
- **GraphQL API**: Modern, type-safe API with comprehensive documentation
- **Interactive Dashboards**: Real-time code intelligence insights
- **Enterprise Architecture**: Production-ready with Docker, Redis, Neo4j

## 📖 Documentation

### GraphQL API Documentation

Our GraphQL API provides comprehensive code intelligence capabilities:

- **🌐 Interactive Documentation**: [`/graphql-docs`](http://localhost:8000/graphql-docs)
- **🛝 GraphQL Playground**: [`/graphql-docs/playground`](http://localhost:8000/graphql-docs/playground)
- **📋 Schema Definition**: [`/graphql-docs/schema.graphql`](http://localhost:8000/graphql-docs/schema.graphql)
- **💡 Query Examples**: [`/graphql-docs/examples.md`](http://localhost:8000/graphql-docs/examples.md)
- **📮 Postman Collection**: [`/graphql-docs/postman`](http://localhost:8000/graphql-docs/postman)

### Quick Start with GraphQL

```graphql
# Analyze a single file
query {
  analyzeFile(input: { filePath: "/src/main.py" }) {
    ... on UniversalFileType {
      path
      language
      totalLines
      nodes {
        id
        name
        type
        displayName
      }
    }
  }
}
```

## 🔧 Development

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- uv (Python package manager)

### Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd ast-viewer
   ```

2. **Start with Docker**:
   ```bash
   docker compose up -d
   ```

3. **Generate Documentation**:
   ```bash
   python3 scripts/generate_docs.py
   ```

4. **Access the API**:
   - API: http://localhost:8000
   - GraphQL Docs: http://localhost:8000/graphql-docs
   - GraphQL Playground: http://localhost:8000/graphql-docs/playground

### Local Development

```bash
# Install dependencies
uv sync --dev

# Run locally
python -m uvicorn src.ast_viewer.api.main:app --reload

# Generate docs
python scripts/generate_docs.py

# Run docs server separately
python src/ast_viewer/api/docs_server.py
```

## 🏗️ Architecture

### Core Components

- **Universal Analyzer**: Multi-language code parsing with Tree-sitter
- **Intelligence Engine**: Advanced relationship analysis with NetworkX
- **Visualization Engine**: Interactive visualizations with Plotly/Matplotlib
- **GraphQL API**: Type-safe API with Strawberry GraphQL
- **Database Layer**: Neo4j for graphs, PostgreSQL for metadata, Redis for caching

### Technology Stack

- **Backend**: FastAPI, Strawberry GraphQL, SQLAlchemy
- **Databases**: Neo4j, PostgreSQL, Redis
- **Analysis**: Tree-sitter, NetworkX, Pydantic
- **Visualization**: Plotly, Matplotlib, Seaborn
- **Infrastructure**: Docker, Gunicorn, Nginx

## 📊 Supported Analysis

### Languages
- Python (`.py`)
- JavaScript (`.js`)
- TypeScript (`.ts`, `.tsx`)
- Go (`.go`)
- Rust (`.rs`)

### Analysis Types
- Code structure and hierarchy
- Complexity metrics
- Dependency relationships
- Call graphs
- Symbol references
- Impact analysis

### Visualization Types
- Dependency graphs
- Call graphs
- Complexity heatmaps
- Architecture maps
- Impact visualizations
- Interactive dashboards

## 🔌 API Integration

### GraphQL Endpoint
```
POST /graphql
Content-Type: application/json

{
  "query": "query { ... }",
  "variables": { ... }
}
```

### Authentication (Optional)
```
Authorization: Bearer <jwt_token>
```

### Rate Limits
- Standard: 100 requests/minute
- Complex queries: 10 requests/minute

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=ast_viewer

# Integration tests
pytest -m integration
```

## 📈 Performance

- **Analysis Speed**: ~1000 LOC/second
- **Memory Usage**: ~500MB for typical projects
- **Cache Hit Rate**: >80% for repeated analysis
- **Concurrent Users**: 50+ supported

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Links

- **API Documentation**: `/graphql-docs`
- **Health Check**: `/health`
- **OpenAPI Docs**: `/docs`
- **GraphQL Schema**: `/graphql-docs/schema.graphql`

---

Built with ❤️ for the soloprenour developer community.
