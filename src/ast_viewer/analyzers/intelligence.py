"""Code Intelligence Engine for relationship analysis and advanced code understanding."""

import hashlib
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import re

try:
    import networkx as nx
except ImportError:
    nx = None

from ..models.universal import (
    UniversalNode,
    UniversalFile,
    Relationship,
    Reference,
    RelationType,
    CodeIntelligence,
    DependencyGraph,
    CallGraphNode,
    ElementType,
    SourceLocation,
    Language,
)

logger = logging.getLogger(__name__)


class IntelligenceEngine:
    """Advanced code intelligence analysis engine."""
    
    def __init__(self):
        self.intelligence_cache: Dict[str, CodeIntelligence] = {}
        
        # NetworkX available check
        if not nx:
            logger.warning("NetworkX not available. Some graph analysis features will be limited.")
    
    def analyze_project_intelligence(self, project_id: str, files: Dict[str, UniversalFile]) -> CodeIntelligence:
        """Perform comprehensive code intelligence analysis on a project."""
        logger.info(f"Starting intelligence analysis for project {project_id}")
        
        # Initialize intelligence store
        intelligence = CodeIntelligence(project_id=project_id)
        
        # Extract all symbols
        self._extract_symbols(intelligence, files)
        
        # Analyze relationships
        self._analyze_relationships(intelligence, files)
        
        # Analyze references
        self._analyze_references(intelligence, files)
        
        # Build call graph
        self._build_call_graph(intelligence)
        
        # Compute graph metrics
        self._compute_graph_metrics(intelligence)
        
        # Cache result
        self.intelligence_cache[project_id] = intelligence
        
        logger.info(f"Intelligence analysis complete: {len(intelligence.symbols)} symbols, "
                   f"{len(intelligence.relationships)} relationships, "
                   f"{sum(len(refs) for refs in intelligence.references.values())} references")
        
        return intelligence
    
    def _extract_symbols(self, intelligence: CodeIntelligence, files: Dict[str, UniversalFile]):
        """Extract all symbols from files into intelligence store."""
        for file_path, file_obj in files.items():
            intelligence.files[file_path] = file_obj
            
            for node in file_obj.nodes:
                intelligence.add_symbol(node)
    
    def _analyze_relationships(self, intelligence: CodeIntelligence, files: Dict[str, UniversalFile]):
        """Analyze relationships between symbols."""
        logger.debug("Analyzing symbol relationships...")
        
        for file_path, file_obj in files.items():
            self._analyze_file_relationships(intelligence, file_obj)
        
        # Cross-file relationship analysis
        self._analyze_cross_file_relationships(intelligence, files)
    
    def _analyze_file_relationships(self, intelligence: CodeIntelligence, file_obj: UniversalFile):
        """Analyze relationships within a single file."""
        nodes = file_obj.nodes
        
        # Analyze inheritance relationships
        for node in nodes:
            if node.type == ElementType.CLASS:
                # Check for extends relationship
                if node.extends:
                    target_node = self._find_symbol_by_name(intelligence, node.extends, file_obj.path)
                    if target_node:
                        relationship = self._create_relationship(
                            node.id, target_node.id, RelationType.EXTENDS, node.location
                        )
                        intelligence.add_relationship(relationship)
                
                # Check for implements relationships
                for interface_name in node.implements:
                    target_node = self._find_symbol_by_name(intelligence, interface_name, file_obj.path)
                    if target_node:
                        relationship = self._create_relationship(
                            node.id, target_node.id, RelationType.IMPLEMENTS, node.location
                        )
                        intelligence.add_relationship(relationship)
        
        # Analyze containment relationships (parent-child)
        for node in nodes:
            if node.parent_id:
                parent_node = intelligence.symbols.get(node.parent_id)
                if parent_node:
                    relationship = self._create_relationship(
                        parent_node.id, node.id, RelationType.CONTAINS, node.location
                    )
                    intelligence.add_relationship(relationship)
                    
                    # Reverse relationship
                    relationship = self._create_relationship(
                        node.id, parent_node.id, RelationType.CONTAINED_IN, node.location
                    )
                    intelligence.add_relationship(relationship)
        
        # Analyze import relationships
        for import_name in file_obj.imports:
            # Find nodes that might be imported symbols
            imported_symbols = self._find_imported_symbols(intelligence, import_name)
            for symbol in imported_symbols:
                # Create import relationship from file to symbol
                file_id = f"file:{file_obj.path}"
                relationship = self._create_relationship(
                    file_id, symbol.id, RelationType.IMPORTS, 
                    location=SourceLocation(
                        file_path=file_obj.path,
                        start_line=1, end_line=1, start_column=0, end_column=0
                    )
                )
                intelligence.add_relationship(relationship)
    
    def _analyze_cross_file_relationships(self, intelligence: CodeIntelligence, files: Dict[str, UniversalFile]):
        """Analyze relationships across different files."""
        # This is where we'd analyze call relationships, but it requires more complex AST analysis
        # For now, we'll implement basic name-based analysis
        
        for file_path, file_obj in files.items():
            for node in file_obj.nodes:
                if node.type in [ElementType.FUNCTION, ElementType.METHOD]:
                    # Analyze potential calls within the node
                    potential_calls = self._extract_potential_calls(node, intelligence)
                    for called_symbol_id in potential_calls:
                        relationship = self._create_relationship(
                            node.id, called_symbol_id, RelationType.CALLS, node.location
                        )
                        intelligence.add_relationship(relationship)
    
    def _analyze_references(self, intelligence: CodeIntelligence, files: Dict[str, UniversalFile]):
        """Analyze symbol references throughout the codebase."""
        logger.debug("Analyzing symbol references...")
        
        # For each symbol, find all potential references
        for symbol_id, symbol in intelligence.symbols.items():
            if not symbol.name:
                continue
                
            # Search for references in all files
            for file_path, file_obj in files.items():
                refs = self._find_references_in_file(symbol, file_obj)
                for ref in refs:
                    intelligence.add_reference(ref)
    
    def _find_references_in_file(self, symbol: UniversalNode, file_obj: UniversalFile) -> List[Reference]:
        """Find references to a symbol within a file."""
        references = []
        
        if not symbol.name:
            return references
        
        # Simple name-based reference finding
        # In a production system, this would use more sophisticated AST analysis
        try:
            content = Path(file_obj.path).read_text(encoding='utf-8')
            lines = content.splitlines()
            
            for line_num, line in enumerate(lines, 1):
                # Find all occurrences of the symbol name
                for match in re.finditer(r'\b' + re.escape(symbol.name) + r'\b', line):
                    # Skip if this is the definition location
                    if (file_obj.path == symbol.location.file_path and 
                        line_num == symbol.location.start_line):
                        continue
                    
                    ref_id = self._generate_reference_id(symbol.id, file_obj.path, line_num, match.start())
                    
                    reference = Reference(
                        id=ref_id,
                        symbol_id=symbol.id,
                        location=SourceLocation(
                            file_path=file_obj.path,
                            start_line=line_num,
                            end_line=line_num,
                            start_column=match.start(),
                            end_column=match.end()
                        ),
                        kind="reference",  # Could be enhanced to detect read/write/call
                        context=line.strip()
                    )
                    references.append(reference)
                    
        except Exception as e:
            logger.warning(f"Failed to analyze references in {file_obj.path}: {e}")
        
        return references
    
    def _extract_potential_calls(self, node: UniversalNode, intelligence: CodeIntelligence) -> List[str]:
        """Extract potential function calls from a node."""
        calls = []
        
        # This is a simplified implementation
        # In production, this would require AST analysis to detect actual function calls
        
        if hasattr(node, 'raw_node') and node.raw_node:
            # For Tree-sitter nodes, we could walk the tree to find call expressions
            # For now, we'll implement a simple heuristic
            pass
        
        return calls
    
    def _build_call_graph(self, intelligence: CodeIntelligence):
        """Build call graph from relationships."""
        logger.debug("Building call graph...")
        
        # Extract call relationships
        call_relationships = [
            rel for rel in intelligence.relationships 
            if rel.type == RelationType.CALLS
        ]
        
        # Build call graph nodes
        for symbol_id, symbol in intelligence.symbols.items():
            if symbol.type in [ElementType.FUNCTION, ElementType.METHOD]:
                call_node = CallGraphNode(
                    symbol_id=symbol_id,
                    symbol_name=symbol.name or "unknown",
                    symbol_type=symbol.type,
                    file_path=symbol.location.file_path,
                    complexity=symbol.complexity
                )
                intelligence.call_graph[symbol_id] = call_node
        
        # Populate call relationships
        for rel in call_relationships:
            if rel.source_id in intelligence.call_graph:
                intelligence.call_graph[rel.source_id].calls.append(rel.target_id)
            
            if rel.target_id in intelligence.call_graph:
                intelligence.call_graph[rel.target_id].called_by.append(rel.source_id)
    
    def _compute_graph_metrics(self, intelligence: CodeIntelligence):
        """Compute graph metrics using NetworkX if available."""
        if not nx or not intelligence.dependency_graph:
            return
        
        try:
            # Create NetworkX graph
            G = nx.DiGraph()
            
            # Add nodes and edges
            for node in intelligence.dependency_graph.nodes:
                G.add_node(node)
            
            for source, target, rel_type in intelligence.dependency_graph.edges:
                G.add_edge(source, target, relation=rel_type.value)
            
            # Compute metrics
            if G.nodes():
                intelligence.dependency_graph.total_nodes = len(G.nodes())
                intelligence.dependency_graph.total_edges = len(G.edges())
                intelligence.dependency_graph.density = nx.density(G)
                intelligence.dependency_graph.strongly_connected_components = nx.number_strongly_connected_components(G)
                
                # Find cycles
                try:
                    cycles = list(nx.simple_cycles(G))
                    intelligence.dependency_graph.cycles = cycles[:10]  # Limit to first 10 cycles
                except:
                    pass  # Cycle detection can be expensive
                
                # Store in intelligence metrics
                intelligence.metrics["graph_metrics"] = {
                    "total_nodes": intelligence.dependency_graph.total_nodes,
                    "total_edges": intelligence.dependency_graph.total_edges,
                    "density": intelligence.dependency_graph.density,
                    "strongly_connected_components": intelligence.dependency_graph.strongly_connected_components,
                    "cycles_found": len(intelligence.dependency_graph.cycles)
                }
                
        except Exception as e:
            logger.error(f"Failed to compute graph metrics: {e}")
    
    def analyze_impact(self, intelligence: CodeIntelligence, symbol_id: str, max_depth: int = 5) -> Dict[str, Any]:
        """Analyze the impact of changing a symbol."""
        if symbol_id not in intelligence.symbols:
            return {"error": "Symbol not found"}
        
        impacted = set()
        queue = [(symbol_id, 0)]
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if depth > max_depth:
                continue
            
            # Find all symbols that depend on current symbol
            dependents = intelligence.get_dependents(current_id)
            for dependent_id in dependents:
                if dependent_id not in impacted:
                    impacted.add(dependent_id)
                    queue.append((dependent_id, depth + 1))
            
            # Also consider references
            references = intelligence.get_symbol_references(current_id)
            for ref in references:
                # Find symbol containing this reference
                containing_symbols = [
                    sym for sym in intelligence.symbols.values()
                    if (sym.location.file_path == ref.location.file_path and
                        sym.location.start_line <= ref.location.start_line <= sym.location.end_line)
                ]
                for sym in containing_symbols:
                    if sym.id not in impacted:
                        impacted.add(sym.id)
        
        # Calculate impact metrics
        impacted_files = set()
        for imp_id in impacted:
            symbol = intelligence.symbols.get(imp_id)
            if symbol:
                impacted_files.add(symbol.location.file_path)
        
        return {
            "total_impacted_symbols": len(impacted),
            "impacted_files": len(impacted_files),
            "impacted_symbols": list(impacted)[:50],  # Limit response size
            "impacted_file_paths": list(impacted_files)
        }
    
    def get_call_graph(self, intelligence: CodeIntelligence, symbol_id: str, depth: int = 3) -> Dict[str, Any]:
        """Get call graph for a symbol."""
        if symbol_id not in intelligence.call_graph:
            return {"error": "Symbol not found in call graph"}
        
        visited = set()
        nodes = []
        edges = []
        
        def traverse(current_id: str, current_depth: int):
            if current_depth > depth or current_id in visited:
                return
            
            visited.add(current_id)
            call_node = intelligence.call_graph.get(current_id)
            if call_node:
                nodes.append({
                    "id": current_id,
                    "name": call_node.symbol_name,
                    "type": call_node.symbol_type.name,
                    "file": call_node.file_path,
                    "complexity": call_node.complexity,
                    "depth": current_depth
                })
                
                # Add outgoing calls
                for called_id in call_node.calls:
                    edges.append({
                        "source": current_id,
                        "target": called_id,
                        "type": "calls"
                    })
                    traverse(called_id, current_depth + 1)
        
        traverse(symbol_id, 0)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "root_symbol": symbol_id,
            "max_depth": depth
        }
    
    # Helper methods
    def _find_symbol_by_name(self, intelligence: CodeIntelligence, name: str, file_path: str) -> Optional[UniversalNode]:
        """Find a symbol by name, preferring symbols in the same file."""
        candidates = []
        
        for symbol in intelligence.symbols.values():
            if symbol.name == name:
                candidates.append(symbol)
        
        # Prefer symbols in the same file
        same_file_candidates = [s for s in candidates if s.location.file_path == file_path]
        if same_file_candidates:
            return same_file_candidates[0]
        
        # Return first candidate if any
        return candidates[0] if candidates else None
    
    def _find_imported_symbols(self, intelligence: CodeIntelligence, import_name: str) -> List[UniversalNode]:
        """Find symbols that might match an import statement."""
        # Simplified import resolution
        symbols = []
        
        # Look for exact name matches
        for symbol in intelligence.symbols.values():
            if symbol.name == import_name:
                symbols.append(symbol)
        
        # Look for module-level matches
        module_parts = import_name.split('.')
        if len(module_parts) > 1:
            last_part = module_parts[-1]
            for symbol in intelligence.symbols.values():
                if symbol.name == last_part:
                    symbols.append(symbol)
        
        return symbols
    
    def _create_relationship(self, source_id: str, target_id: str, rel_type: RelationType, 
                           location: Optional[SourceLocation] = None) -> Relationship:
        """Create a relationship between two symbols."""
        rel_id = hashlib.md5(f"{source_id}:{target_id}:{rel_type.value}".encode()).hexdigest()[:16]
        
        return Relationship(
            id=rel_id,
            source_id=source_id,
            target_id=target_id,
            type=rel_type,
            location=location
        )
    
    def _generate_reference_id(self, symbol_id: str, file_path: str, line: int, column: int) -> str:
        """Generate unique reference ID."""
        ref_string = f"{symbol_id}:{file_path}:{line}:{column}"
        return hashlib.md5(ref_string.encode()).hexdigest()[:16]
