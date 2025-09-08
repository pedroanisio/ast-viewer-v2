"""Python AST adapter for Universal Code Analysis Model."""

import ast
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from ..models.universal import (
    ElementType,
    Language,
    SourceLocation,
    UniversalNode,
    UniversalFile,
)
from ..common.identifiers import IDGenerator
from ..common.errors import handle_errors, analysis_operation
from ..common.metrics import ComplexityCalculator

logger = logging.getLogger(__name__)


class PythonAdapter:
    """Adapter for Python AST to Universal model."""
    
    @analysis_operation(default_return=None)
    def parse_file(self, file_path: Path, content: str) -> UniversalFile:
        """Parse Python file into universal format."""
        tree = ast.parse(content, filename=str(file_path))
        
        universal_file = UniversalFile(
            path=str(file_path),
            language=Language.PYTHON,
            encoding='utf-8',
            size_bytes=len(content.encode('utf-8')),
            hash=IDGenerator.generate_file_hash(content),
            total_lines=len(content.splitlines())
        )
        
        # Extract nodes
        nodes = self.extract_nodes(tree, str(file_path))
        for node in nodes:
            universal_file.add_node(node)
        
        # Extract imports
        universal_file.imports = self._extract_imports(tree)
        
        # Calculate metrics
        universal_file.complexity = self._calculate_complexity(tree)
        universal_file.code_lines = self._count_code_lines(content)
        
        return universal_file
    
    def extract_nodes(self, tree: ast.AST, file_path: str) -> List[UniversalNode]:
        """Extract universal nodes from Python AST."""
        nodes = []
        node_stack = [(tree, None)]  # (node, parent_id)
        
        while node_stack:
            node, parent_id = node_stack.pop()
            
            # Create universal node
            universal_node = self._create_universal_node(node, file_path, parent_id)
            if universal_node:
                nodes.append(universal_node)
                
                # Add children to stack
                for child in ast.iter_child_nodes(node):
                    node_stack.append((child, universal_node.id))
        
        return nodes
    
    def _create_universal_node(self, node: ast.AST, file_path: str, 
                               parent_id: Optional[str]) -> Optional[UniversalNode]:
        """Convert Python AST node to universal node."""
        node_type = self._map_node_type(node)
        if not node_type:
            return None
        
        # Generate unique ID
        location = SourceLocation.from_ast_node(node, file_path)
        node_id = self._generate_node_id(node, location)
        
        # Extract name
        name = self._extract_node_name(node)
        
        # Create universal node
        universal_node = UniversalNode(
            id=node_id,
            type=node_type,
            name=name,
            language=Language.PYTHON,
            location=location,
            parent_id=parent_id,
            raw_node=node
        )
        
        # Add Python-specific properties
        self._add_python_properties(universal_node, node)
        
        return universal_node
    
    def _map_node_type(self, node: ast.AST) -> Optional[ElementType]:
        """Map Python AST node to universal element type."""
        mapping = {
            ast.Module: ElementType.MODULE,
            ast.ClassDef: ElementType.CLASS,
            ast.FunctionDef: ElementType.FUNCTION,
            ast.AsyncFunctionDef: ElementType.FUNCTION,
            ast.Assign: ElementType.VARIABLE,
            ast.AnnAssign: ElementType.VARIABLE,
            ast.Import: ElementType.IMPORT,
            ast.ImportFrom: ElementType.IMPORT,
            ast.If: ElementType.CONDITIONAL,
            ast.For: ElementType.LOOP,
            ast.While: ElementType.LOOP,
            ast.Try: ElementType.EXCEPTION,
            ast.Lambda: ElementType.LAMBDA,
            ast.GeneratorExp: ElementType.GENERATOR,
        }
        
        for ast_type, element_type in mapping.items():
            if isinstance(node, ast_type):
                return element_type
        return None
    
    def _extract_node_name(self, node: ast.AST) -> Optional[str]:
        """Extract name from Python AST node."""
        for attr in ['name', 'id', 'arg', 'attr']:
            if hasattr(node, attr):
                return str(getattr(node, attr))
        
        if isinstance(node, ast.Assign) and node.targets:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                return target.id
        
        return None
    
    def _add_python_properties(self, universal_node: UniversalNode, ast_node: ast.AST) -> None:
        """Add Python-specific properties to universal node."""
        if isinstance(ast_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            universal_node.is_async = isinstance(ast_node, ast.AsyncFunctionDef)
            universal_node.parameters = self._extract_parameters(ast_node)
            universal_node.return_type = self._extract_return_type(ast_node)
            universal_node.complexity = self._calculate_node_complexity(ast_node)
            
            # Check for decorators
            if ast_node.decorator_list:
                decorators = [self._get_decorator_name(d) for d in ast_node.decorator_list]
                universal_node.annotations['decorators'] = decorators
                
                # Check for common decorators
                if 'staticmethod' in decorators:
                    universal_node.is_static = True
                if 'abstractmethod' in decorators:
                    universal_node.is_abstract = True
        
        elif isinstance(ast_node, ast.ClassDef):
            # Extract base classes
            if ast_node.bases:
                base_names = [self._get_base_name(base) for base in ast_node.bases]
                if base_names:
                    universal_node.extends = base_names[0]
                    if len(base_names) > 1:
                        universal_node.implements = set(base_names[1:])
    
    def _extract_parameters(self, func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> List[Dict[str, Any]]:
        """Extract function parameters."""
        params = []
        for arg in func_node.args.args:
            param = {
                'name': arg.arg,
                'type': None,
                'default': None
            }
            if arg.annotation:
                param['type'] = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)
            params.append(param)
        return params
    
    def _extract_return_type(self, func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Optional[str]:
        """Extract function return type."""
        if func_node.returns:
            return ast.unparse(func_node.returns) if hasattr(ast, 'unparse') else str(func_node.returns)
        return None
    
    def _calculate_node_complexity(self, node: ast.AST) -> float:
        """Calculate cyclomatic complexity for a node using centralized calculator."""
        # Convert AST node to data format expected by ComplexityCalculator
        node_data = {
            'type': node.__class__.__name__.lower(),
            'children': [{'type': child.__class__.__name__.lower()} for child in ast.walk(node)]
        }
        return ComplexityCalculator.calculate_cyclomatic_complexity(node_data)
    
    def _generate_node_id(self, node: ast.AST, location: SourceLocation) -> str:
        """Generate unique node ID."""
        return IDGenerator.generate_node_id(
            location.file_path,
            location.start_line,
            location.start_column,
            node.__class__.__name__
        )
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        return imports
    
    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate average complexity for file."""
        complexities = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexities.append(self._calculate_node_complexity(node))
        return sum(complexities) / len(complexities) if complexities else 1.0
    
    def _count_code_lines(self, content: str) -> int:
        """Count actual code lines (non-blank, non-comment)."""
        code_lines = 0
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                code_lines += 1
        return code_lines
    
    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Extract decorator name."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
        return str(decorator)
    
    def _get_base_name(self, base: ast.AST) -> str:
        """Extract base class name."""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return f"{self._get_base_name(base.value)}.{base.attr}"
        return str(base)
