"""Tree-sitter adapter for multi-language code analysis."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict

try:
    import tree_sitter
except ImportError:
    tree_sitter = None

from ..models.universal import (
    ElementType,
    Language,
    SourceLocation,
    UniversalNode,
    UniversalFile,
)
from ..common.identifiers import IDGenerator
from ..common.metrics import ComplexityCalculator

logger = logging.getLogger(__name__)


class TreeSitterAdapter:
    """Multi-language adapter using Tree-sitter."""
    
    def __init__(self):
        self.parsers: Dict[Language, tree_sitter.Parser] = {}
        self.query_cache: Dict[str, tree_sitter.Query] = {}
        self._init_parsers()
    
    def _init_parsers(self):
        """Initialize Tree-sitter parsers for all supported languages."""
        if not tree_sitter:
            logger.warning("Tree-sitter not available. Install tree-sitter to enable multi-language support.")
            return
            
        for language in Language:
            parser_lib = language.tree_sitter_parser
            if parser_lib:
                try:
                    parser = tree_sitter.Parser()
                    parser.language = parser_lib
                    self.parsers[language] = parser
                    logger.debug(f"Initialized Tree-sitter parser for {language.value}")
                except Exception as e:
                    logger.warning(f"Failed to initialize parser for {language.value}: {e}")
    
    def parse_file(self, file_path: Path, content: str) -> UniversalFile:
        """Parse file using Tree-sitter."""
        # Detect language
        language = self._detect_language(file_path)
        
        if language not in self.parsers:
            raise ValueError(f"No Tree-sitter parser available for {language.value}")
        
        try:
            # Parse with Tree-sitter
            content_bytes = content.encode('utf-8')
            parser = self.parsers[language]
            tree = parser.parse(content_bytes)
            
            # Create universal file
            universal_file = UniversalFile(
                path=str(file_path),
                language=language,
                encoding='utf-8',
                size_bytes=len(content_bytes),
                hash=IDGenerator.generate_file_hash(content_bytes),
                total_lines=len(content.splitlines())
            )
            
            # Extract symbols/nodes
            nodes = self.extract_nodes(tree, content_bytes, str(file_path), language)
            for node in nodes:
                universal_file.add_node(node)
            
            # Extract imports/exports
            universal_file.imports = self._extract_imports(tree, content_bytes, language)
            universal_file.exports = self._extract_exports(tree, content_bytes, language)
            
            # Calculate metrics
            universal_file.code_lines = self._count_code_lines(content)
            universal_file.complexity = self._calculate_file_complexity(nodes)
            
            return universal_file
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path} with Tree-sitter: {e}")
            raise
    
    def extract_nodes(self, tree: tree_sitter.Tree, content: bytes, 
                     file_path: str, language: Language) -> List[UniversalNode]:
        """Extract nodes from Tree-sitter tree using both queries and tree walking."""
        nodes = []
        
        # Try query-based extraction first (more accurate)
        try:
            query_nodes = self._extract_nodes_with_query(tree, content, language, file_path)
            if query_nodes:
                nodes.extend(query_nodes)
                logger.debug(f"Extracted {len(query_nodes)} nodes using queries for {language.value}")
        except Exception as e:
            logger.warning(f"Query-based extraction failed for {language.value}: {e}")
        
        # Fallback to tree walking if queries fail or return no results
        if not nodes:
            nodes = self._extract_nodes_by_walking(tree, content, language, file_path)
            logger.debug(f"Extracted {len(nodes)} nodes using tree walking for {language.value}")
        
        # Build hierarchy
        self._build_node_hierarchy(nodes)
        
        return nodes
    
    def _extract_nodes_with_query(self, tree: tree_sitter.Tree, content: bytes,
                                 language: Language, file_path: str) -> List[UniversalNode]:
        """Extract nodes using Tree-sitter queries."""
        nodes = []
        
        # Get language-specific query
        query = self._get_symbol_query(language)
        if not query:
            return nodes
        
        # Create query cursor and execute query
        cursor = tree_sitter.QueryCursor()
        captures = cursor.captures(query, tree.root_node)
        
        # Process captures
        for capture in captures:
            node, capture_name = capture
            universal_node = self._create_universal_node_from_capture(
                node, capture_name, content, language, file_path
            )
            if universal_node:
                nodes.append(universal_node)
        
        return nodes
    
    def _extract_nodes_by_walking(self, tree: tree_sitter.Tree, content: bytes,
                                 language: Language, file_path: str) -> List[UniversalNode]:
        """Extract nodes by walking the Tree-sitter AST."""
        nodes = []
        
        # Get symbol types for this language
        symbol_types = self._get_symbol_types(language)
        
        # Walk the tree and extract symbols
        def walk_tree(node: tree_sitter.Node, depth: int = 0):
            # Check if this node represents a symbol we care about
            element_type = symbol_types.get(node.type)
            if element_type:
                universal_node = self._create_universal_node_from_type(
                    node, element_type, content, language, file_path
                )
                if universal_node:
                    nodes.append(universal_node)
            
            # Recursively walk children
            for child in node.children:
                walk_tree(child, depth + 1)
        
        # Start walking from root
        walk_tree(tree.root_node)
        
        return nodes
    
    def _get_symbol_types(self, language: Language) -> Dict[str, ElementType]:
        """Get mapping of Tree-sitter node types to ElementTypes for a language."""
        type_mappings = {
            Language.PYTHON: {
                "class_definition": ElementType.CLASS,
                "function_definition": ElementType.FUNCTION,
                "assignment": ElementType.VARIABLE,
                "import_statement": ElementType.IMPORT,
                "import_from_statement": ElementType.IMPORT,
            },
            Language.JAVASCRIPT: {
                "class_declaration": ElementType.CLASS,
                "function_declaration": ElementType.FUNCTION,
                "method_definition": ElementType.METHOD,
                "variable_declarator": ElementType.VARIABLE,
                "import_statement": ElementType.IMPORT,
                "export_statement": ElementType.EXPORT,
            },
            Language.TYPESCRIPT: {
                "class_declaration": ElementType.CLASS,
                "interface_declaration": ElementType.INTERFACE,
                "function_declaration": ElementType.FUNCTION,
                "method_definition": ElementType.METHOD,
                "variable_declarator": ElementType.VARIABLE,
                "type_alias_declaration": ElementType.CLASS,
                "import_statement": ElementType.IMPORT,
                "export_statement": ElementType.EXPORT,
            },
            Language.GO: {
                "type_declaration": ElementType.CLASS,
                "function_declaration": ElementType.FUNCTION,
                "method_declaration": ElementType.METHOD,
                "var_declaration": ElementType.VARIABLE,
                "const_declaration": ElementType.CONSTANT,
                "import_declaration": ElementType.IMPORT,
            },
            Language.RUST: {
                "struct_item": ElementType.STRUCT,
                "enum_item": ElementType.ENUM,
                "trait_item": ElementType.TRAIT,
                "function_item": ElementType.FUNCTION,
                "impl_item": ElementType.CLASS,
                "use_declaration": ElementType.IMPORT,
            },
        }
        
        return type_mappings.get(language, {})
    
    def _create_universal_node_from_type(self, node: tree_sitter.Node, element_type: ElementType,
                                        content: bytes, language: Language, file_path: str) -> Optional[UniversalNode]:
        """Create UniversalNode from Tree-sitter node with known element type."""
        # Extract name
        name = self._extract_node_name(node, content)
        if not name and element_type not in [ElementType.IMPORT, ElementType.EXPORT]:
            return None
        
        # Create location
        location = SourceLocation.from_tree_sitter_node(node, file_path)
        
        # Generate unique ID
        node_id = self._generate_node_id(file_path, name or node.type, location)
        
        # Create universal node
        universal_node = UniversalNode(
            id=node_id,
            type=element_type,
            name=name,
            language=language,
            location=location,
            tree_sitter_type=node.type,
            lines_of_code=location.end_line - location.start_line + 1,
            raw_node=node
        )
        
        # Extract additional properties
        self._extract_node_properties(universal_node, node, content, language)
        
        return universal_node
    
    def _get_symbol_query(self, language: Language) -> Optional[tree_sitter.Query]:
        """Get Tree-sitter query for extracting symbols."""
        queries = {
            Language.PYTHON: """
                (class_definition name: (identifier) @class)
                (function_definition name: (identifier) @function)
                (assignment left: (identifier) @variable)
                (import_statement) @import
                (import_from_statement) @import
            """,
            Language.JAVASCRIPT: """
                (class_declaration name: (identifier) @class)
                (function_declaration name: (identifier) @function)
                (method_definition name: (property_identifier) @method)
                (variable_declarator name: (identifier) @variable)
                (import_statement) @import
                (export_statement) @export
            """,
            Language.TYPESCRIPT: """
                (class_declaration name: (type_identifier) @class)
                (interface_declaration name: (type_identifier) @interface)
                (function_declaration name: (identifier) @function)
                (method_definition name: (property_identifier) @method)
                (variable_declarator name: (identifier) @variable)
                (type_alias_declaration name: (type_identifier) @type)
                (import_statement) @import
                (export_statement) @export
            """,
            Language.GO: """
                (type_declaration (type_spec name: (type_identifier) @type))
                (function_declaration name: (identifier) @function)
                (method_declaration name: (field_identifier) @method)
                (var_declaration (var_spec name: (identifier) @variable))
                (const_declaration (const_spec name: (identifier) @constant))
                (import_declaration) @import
            """,
            Language.RUST: """
                (struct_item name: (type_identifier) @struct)
                (enum_item name: (type_identifier) @enum)
                (trait_item name: (type_identifier) @trait)
                (function_item name: (identifier) @function)
                (impl_item) @impl
                (use_declaration) @import
            """,
        }
        
        query_text = queries.get(language)
        if not query_text:
            return None
        
        cache_key = f"{language.value}_symbols"
        if cache_key not in self.query_cache:
            try:
                ts_language = language.tree_sitter_parser
                if ts_language:
                    # Use the new Query constructor as recommended by the documentation
                    self.query_cache[cache_key] = tree_sitter.Query(ts_language, query_text)
            except Exception as e:
                logger.error(f"Failed to create query for {language.value}: {e}")
                return None
        
        return self.query_cache.get(cache_key)
    
    def _create_universal_node_from_capture(self, node: tree_sitter.Node, capture_name: str,
                                           content: bytes, language: Language, file_path: str) -> Optional[UniversalNode]:
        """Create UniversalNode from Tree-sitter capture."""
        # Map capture names to element types
        element_type_map = {
            "class": ElementType.CLASS,
            "interface": ElementType.INTERFACE,
            "function": ElementType.FUNCTION,
            "method": ElementType.METHOD,
            "variable": ElementType.VARIABLE,
            "constant": ElementType.CONSTANT,
            "struct": ElementType.STRUCT,
            "enum": ElementType.ENUM,
            "trait": ElementType.TRAIT,
            "type": ElementType.CLASS,  # Generic type mapping
            "import": ElementType.IMPORT,
            "export": ElementType.EXPORT,
            "impl": ElementType.CLASS,  # Rust impl blocks
        }
        
        element_type = element_type_map.get(capture_name)
        if not element_type:
            return None
        
        # Extract name
        name = self._extract_node_name(node, content)
        if not name and element_type not in [ElementType.IMPORT, ElementType.EXPORT]:
            return None
        
        # Create location
        location = SourceLocation.from_tree_sitter_node(node, file_path)
        
        # Generate unique ID
        node_id = self._generate_node_id(file_path, name or node.type, location)
        
        # Create universal node
        universal_node = UniversalNode(
            id=node_id,
            type=element_type,
            name=name,
            language=language,
            location=location,
            tree_sitter_type=node.type,
            lines_of_code=location.end_line - location.start_line + 1,
            raw_node=node
        )
        
        # Extract additional properties
        self._extract_node_properties(universal_node, node, content, language)
        
        return universal_node
    
    def _extract_node_name(self, node: tree_sitter.Node, content: bytes) -> Optional[str]:
        """Extract name from Tree-sitter node."""
        # Look for identifier nodes
        name_types = ["identifier", "type_identifier", "property_identifier", "field_identifier"]
        
        def find_name(n: tree_sitter.Node) -> Optional[str]:
            if n.type in name_types:
                return content[n.start_byte:n.end_byte].decode('utf-8', errors='ignore')
            
            for child in n.children:
                if child.type in name_types:
                    return content[child.start_byte:child.end_byte].decode('utf-8', errors='ignore')
                # Recursive search for nested names
                nested_name = find_name(child)
                if nested_name:
                    return nested_name
            return None
        
        return find_name(node)
    
    def _extract_node_properties(self, universal_node: UniversalNode, 
                                 node: tree_sitter.Node, content: bytes, language: Language):
        """Extract language-specific properties from Tree-sitter node."""
        # Extract modifiers
        modifiers = self._find_modifiers(node, content)
        
        if "static" in modifiers:
            universal_node.is_static = True
        if "async" in modifiers:
            universal_node.is_async = True
        if "abstract" in modifiers:
            universal_node.is_abstract = True
        if "final" in modifiers or "sealed" in modifiers:
            universal_node.is_final = True
        if "const" in modifiers or "readonly" in modifiers:
            universal_node.is_const = True
        
        # Extract visibility
        visibility = self._extract_visibility(node, content)
        if visibility:
            from ..models.universal import AccessLevel
            try:
                universal_node.access_level = AccessLevel(visibility)
            except ValueError:
                pass  # Unknown visibility level
        
        # Calculate complexity
        universal_node.complexity = self._calculate_node_complexity(node)
        universal_node.cognitive_complexity = self._calculate_cognitive_complexity(node)
        
        # Extract parameters for functions/methods
        if universal_node.type in [ElementType.FUNCTION, ElementType.METHOD]:
            universal_node.parameters = self._extract_parameters(node, content, language)
    
    def _find_modifiers(self, node: tree_sitter.Node, content: bytes) -> Set[str]:
        """Find modifier keywords in node."""
        modifiers = set()
        modifier_keywords = {
            "static", "async", "abstract", "final", "sealed", 
            "const", "readonly", "public", "private", "protected"
        }
        
        def search_modifiers(n: tree_sitter.Node):
            node_text = content[n.start_byte:n.end_byte].decode('utf-8', errors='ignore')
            if node_text.lower() in modifier_keywords:
                modifiers.add(node_text.lower())
            
            for child in n.children:
                search_modifiers(child)
        
        search_modifiers(node)
        return modifiers
    
    def _extract_visibility(self, node: tree_sitter.Node, content: bytes) -> Optional[str]:
        """Extract visibility/access level from node."""
        visibility_keywords = ["public", "private", "protected", "internal", "package"]
        
        def find_visibility(n: tree_sitter.Node) -> Optional[str]:
            node_text = content[n.start_byte:n.end_byte].decode('utf-8', errors='ignore')
            if node_text.lower() in visibility_keywords:
                return node_text.lower()
            
            for child in n.children:
                vis = find_visibility(child)
                if vis:
                    return vis
            return None
        
        return find_visibility(node)
    
    def _extract_parameters(self, node: tree_sitter.Node, content: bytes, 
                           language: Language) -> List[Dict[str, Any]]:
        """Extract function parameters."""
        params = []
        
        # Find parameter list
        param_list_types = ["parameters", "parameter_list", "formal_parameters"]
        param_list = None
        
        def find_param_list(n: tree_sitter.Node):
            if n.type in param_list_types:
                return n
            for child in n.children:
                result = find_param_list(child)
                if result:
                    return result
            return None
        
        param_list = find_param_list(node)
        if not param_list:
            return params
        
        # Extract individual parameters
        position = 0
        for child in param_list.children:
            if "parameter" in child.type or child.type in ["identifier", "typed_parameter"]:
                param_name = self._extract_node_name(child, content)
                if param_name:
                    param = {
                        "name": param_name,
                        "type": None,
                        "default": None,
                        "position": position
                    }
                    
                    # Try to extract type information
                    type_info = self._extract_type_from_node(child, content)
                    if type_info:
                        param["type"] = type_info
                    
                    params.append(param)
                    position += 1
        
        return params
    
    def _extract_type_from_node(self, node: tree_sitter.Node, content: bytes) -> Optional[str]:
        """Extract type information from node."""
        type_node_types = ["type", "type_annotation", "type_identifier", "primitive_type"]
        
        def find_type(n: tree_sitter.Node) -> Optional[str]:
            if n.type in type_node_types:
                return content[n.start_byte:n.end_byte].decode('utf-8', errors='ignore')
            
            for child in n.children:
                if child.type in type_node_types:
                    return content[child.start_byte:child.end_byte].decode('utf-8', errors='ignore')
            return None
        
        return find_type(node)
    
    def _calculate_node_complexity(self, node: tree_sitter.Node) -> float:
        """Calculate cyclomatic complexity using centralized calculator."""
        # Convert tree-sitter node to data format expected by ComplexityCalculator
        node_data = {
            'type': node.type,
            'children': self._convert_tree_sitter_children(node)
        }
        return ComplexityCalculator.calculate_cyclomatic_complexity(node_data)
    
    def _convert_tree_sitter_children(self, node: tree_sitter.Node) -> list:
        """Convert tree-sitter node children to data format."""
        children = []
        for child in node.children:
            children.append({'type': child.type})
        return children
    
    def _calculate_cognitive_complexity(self, node: tree_sitter.Node) -> int:
        """Calculate cognitive complexity using centralized calculator."""
        # Convert tree-sitter node to data format expected by ComplexityCalculator
        nesting_level = self._calculate_nesting_level(node)
        node_data = {
            'type': node.type,
            'nesting_level': nesting_level,
            'children': self._convert_tree_sitter_children(node)
        }
        return int(ComplexityCalculator.calculate_cognitive_complexity(node_data))
    
    def _calculate_nesting_level(self, node: tree_sitter.Node) -> int:
        """Calculate nesting level for a node."""
        level = 0
        parent = node.parent
        while parent:
            if parent.type in ["if_statement", "while_statement", "for_statement", "function_definition", "method_definition"]:
                level += 1
            parent = parent.parent
        return level
    
    def _build_node_hierarchy(self, nodes: List[UniversalNode]):
        """Build parent-child relationships between nodes."""
        # Sort by byte position for efficient hierarchy building
        nodes_by_position = sorted(nodes, key=lambda n: (n.location.start_byte or 0, n.location.end_byte or 0))
        
        for i, node in enumerate(nodes_by_position):
            # Find the most immediate parent
            for j in range(i - 1, -1, -1):
                potential_parent = nodes_by_position[j]
                
                # Check if node is contained within potential_parent
                if (potential_parent.location.start_byte is not None and 
                    node.location.start_byte is not None and
                    potential_parent.location.start_byte <= node.location.start_byte and
                    potential_parent.location.end_byte >= node.location.end_byte and
                    potential_parent != node):
                    
                    # This is the immediate parent
                    node.parent_id = potential_parent.id
                    if node.id not in potential_parent.children_ids:
                        potential_parent.children_ids.append(node.id)
                    break
    
    def _extract_imports(self, tree: tree_sitter.Tree, content: bytes, language: Language) -> List[str]:
        """Extract import statements."""
        imports = []
        
        import_queries = {
            Language.PYTHON: "(import_statement) @import (import_from_statement) @import",
            Language.JAVASCRIPT: "(import_statement) @import",
            Language.TYPESCRIPT: "(import_statement) @import",
            Language.GO: "(import_declaration) @import",
            Language.RUST: "(use_declaration) @import",
        }
        
        query_text = import_queries.get(language)
        if not query_text:
            return imports
        
        try:
            parser_lib = language.tree_sitter_parser
            if parser_lib:
                query = parser_lib.query(query_text)
                captures = query.captures(tree.root_node)
                
                for node, _ in captures:
                    import_text = content[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
                    # Extract just the module name (simplified)
                    import_name = self._parse_import_statement(import_text, language)
                    if import_name:
                        imports.append(import_name)
        except Exception as e:
            logger.warning(f"Failed to extract imports for {language.value}: {e}")
        
        return imports
    
    def _extract_exports(self, tree: tree_sitter.Tree, content: bytes, language: Language) -> List[str]:
        """Extract export statements."""
        exports = []
        
        # Only JavaScript/TypeScript typically have explicit exports
        if language not in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return exports
        
        try:
            parser_lib = language.tree_sitter_parser
            if parser_lib:
                query = parser_lib.query("(export_statement) @export")
                captures = query.captures(tree.root_node)
                
                for node, _ in captures:
                    export_text = content[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
                    export_name = self._parse_export_statement(export_text)
                    if export_name:
                        exports.append(export_name)
        except Exception as e:
            logger.warning(f"Failed to extract exports for {language.value}: {e}")
        
        return exports
    
    def _parse_import_statement(self, import_text: str, language: Language) -> Optional[str]:
        """Parse import statement to extract module name."""
        # Simplified parsing - would need more sophisticated logic
        if language == Language.PYTHON:
            if import_text.startswith("import "):
                return import_text.replace("import ", "").strip().split()[0]
            elif "from " in import_text:
                parts = import_text.split()
                if len(parts) >= 2:
                    return parts[1]
        elif language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            if "from " in import_text:
                # Extract string after 'from'
                parts = import_text.split("from ")
                if len(parts) > 1:
                    module = parts[1].strip().strip("';\"")
                    return module
        
        return None
    
    def _parse_export_statement(self, export_text: str) -> Optional[str]:
        """Parse export statement to extract exported name."""
        # Simplified parsing
        if "export " in export_text:
            return "exported_item"  # Placeholder
        return None
    
    def _count_code_lines(self, content: str) -> int:
        """Count non-empty, non-comment lines."""
        code_lines = 0
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not self._is_comment_line(stripped):
                code_lines += 1
        return code_lines
    
    def _is_comment_line(self, line: str) -> bool:
        """Check if line is a comment."""
        comment_markers = ['#', '//', '/*', '*', '<!--', '--', '///', '##']
        return any(line.startswith(marker) for marker in comment_markers)
    
    def _calculate_file_complexity(self, nodes: List[UniversalNode]) -> float:
        """Calculate average complexity for file."""
        complexities = [node.complexity for node in nodes 
                       if node.type in [ElementType.FUNCTION, ElementType.METHOD]]
        return sum(complexities) / len(complexities) if complexities else 1.0
    
    def _detect_language(self, file_path: Path) -> Language:
        """Detect language from file extension."""
        # Use centralized language detection (DRY fix)
        from ..common.language_utils import LanguageDetector
        return LanguageDetector.detect_from_path(file_path)
    
    def _generate_node_id(self, file_path: str, name: str, location: SourceLocation) -> str:
        """Generate unique node ID using centralized utility."""
        from ..common.identifiers import IDGenerator
        return IDGenerator.generate_node_id(
            file_path, name, location.start_line, 
            location.start_column, location.start_byte or 0
        )
