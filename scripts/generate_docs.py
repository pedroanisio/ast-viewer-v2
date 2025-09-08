#!/usr/bin/env python3
"""
Generate comprehensive GraphQL API documentation.

This script generates all documentation formats for the AST Viewer GraphQL API
including SDL, JSON schema, examples, interactive docs, and more.
"""

import sys
import os
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ast_viewer.graphql.docs_generator import GraphQLDocumentationGenerator


def main():
    """Generate all documentation."""
    print("🚀 Generating GraphQL API Documentation...")
    print("=" * 50)
    
    # Create output directory
    docs_dir = Path(__file__).parent.parent / "docs" / "graphql"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize generator
    generator = GraphQLDocumentationGenerator(str(docs_dir))
    
    try:
        # Generate all documentation
        files = generator.generate_all_docs()
        
        print("✅ Successfully generated documentation files:")
        print()
        
        for name, path in files.items():
            relative_path = Path(path).relative_to(Path.cwd())
            print(f"📄 {name:25} → {relative_path}")
        
        print()
        print("📚 Documentation Overview:")
        print(f"   • Interactive Docs:    {relative_path.parent}/interactive.html")
        print(f"   • GraphQL Schema:      {relative_path.parent}/schema.graphql")
        print(f"   • JSON Schema:         {relative_path.parent}/schema.json")
        print(f"   • Query Examples:      {relative_path.parent}/examples.md")
        print(f"   • API Reference:       {relative_path.parent}/api-reference.md")
        print(f"   • Postman Collection:  {relative_path.parent}/postman_collection.json")
        
        print()
        print("🎯 Next Steps:")
        print("   1. Open interactive.html in your browser")
        print("   2. Import postman_collection.json into Postman")
        print("   3. Use schema.graphql for code generation")
        print("   4. Share examples.md with API users")
        
        print()
        print("🌐 To serve interactive docs:")
        print("   python -m ast_viewer.api.docs_server")
        print("   Then visit: http://localhost:8001/")
        
    except Exception as e:
        print(f"❌ Error generating documentation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
