"""Integrated code analyzer combining universal analysis with project-level insights."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from .universal import UniversalAnalyzer
from .intelligence import IntelligenceEngine
from ..models.universal import ElementType, UniversalFile, CodeIntelligence
from ..visualizations.engine import VisualizationEngine, VisualizationType

logger = logging.getLogger(__name__)


class IntegratedCodeAnalyzer:
    """High-level analyzer integrating all components."""
    
    def __init__(self, cache_manager=None):
        self.universal_analyzer = UniversalAnalyzer()
        self.intelligence_engine = IntelligenceEngine()
        self.visualization_engine = VisualizationEngine()
        self.cache = cache_manager
        
        # Import existing components if available
        try:
            from repository_analyzer import RepositoryAnalyzer
            self.legacy_ast_analyzer = RepositoryAnalyzer(cache_manager)
        except ImportError:
            self.legacy_ast_analyzer = None
        
        try:
            from project_builder import ProjectBuilder
            self.project_builder = ProjectBuilder(cache_manager)
        except ImportError:
            self.project_builder = None
    
    def analyze_project(self, project_path: Union[str, Path], 
                        project_name: str = None) -> Dict[str, Any]:
        """Complete project analysis using universal model with code intelligence."""
        project_path = Path(project_path)
        project_name = project_name or project_path.name
        project_id = f"project:{project_name}"
        
        logger.info(f"Starting comprehensive analysis of {project_name}")
        
        # Analyze all files
        file_analyses = self.universal_analyzer.analyze_directory(project_path)
        
        # Perform intelligence analysis
        intelligence = self.intelligence_engine.analyze_project_intelligence(project_id, file_analyses)
        
        # Build project structure
        project_data = self._build_project_structure(project_path, project_name, file_analyses)
        
        # Calculate project metrics (enhanced with intelligence)
        metrics = self._calculate_enhanced_metrics(file_analyses, intelligence)
        
        # Build dependency graph
        dependencies = self._analyze_dependencies(file_analyses)
        
        return {
            'project': project_data,
            'files': {path: file.model_dump() for path, file in file_analyses.items()},
            'metrics': metrics,
            'dependencies': dependencies,
            'languages': self._get_language_distribution(file_analyses),
            'intelligence': {
                'total_symbols': len(intelligence.symbols),
                'total_relationships': len(intelligence.relationships),
                'total_references': sum(len(refs) for refs in intelligence.references.values()),
                'call_graph_nodes': len(intelligence.call_graph),
                'graph_metrics': intelligence.metrics.get('graph_metrics', {}),
                'dependency_graph': intelligence.dependency_graph.model_dump() if intelligence.dependency_graph else None
            }
        }
    
    def get_intelligence(self, project_id: str) -> Optional[CodeIntelligence]:
        """Get cached intelligence analysis for a project."""
        return self.intelligence_engine.intelligence_cache.get(project_id)
    
    def analyze_symbol_impact(self, project_id: str, symbol_id: str, max_depth: int = 5) -> Dict[str, Any]:
        """Analyze the impact of changing a symbol."""
        intelligence = self.get_intelligence(project_id)
        if not intelligence:
            return {"error": "Project not analyzed"}
        
        return self.intelligence_engine.analyze_impact(intelligence, symbol_id, max_depth)
    
    def get_symbol_call_graph(self, project_id: str, symbol_id: str, depth: int = 3) -> Dict[str, Any]:
        """Get call graph for a symbol."""
        intelligence = self.get_intelligence(project_id)
        if not intelligence:
            return {"error": "Project not analyzed"}
        
        return self.intelligence_engine.get_call_graph(intelligence, symbol_id, depth)
    
    def find_symbol_references(self, project_id: str, symbol_id: str) -> List[Dict[str, Any]]:
        """Find all references to a symbol."""
        intelligence = self.get_intelligence(project_id)
        if not intelligence:
            return []
        
        references = intelligence.get_symbol_references(symbol_id)
        return [ref.model_dump() for ref in references]
    
    def get_symbol_relationships(self, project_id: str, symbol_id: str, 
                               relationship_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get relationships for a symbol."""
        intelligence = self.get_intelligence(project_id)
        if not intelligence:
            return []
        
        from ..models.universal import RelationType
        rel_types = None
        if relationship_types:
            rel_types = [RelationType(t) for t in relationship_types if t in RelationType.__members__.values()]
        
        relationships = intelligence.get_symbol_relationships(symbol_id, rel_types)
        return [rel.model_dump() for rel in relationships]
    
    def generate_visualization(self, project_id: str, visualization_type: str, **kwargs) -> Dict[str, Any]:
        """Generate a visualization for the project."""
        intelligence = self.get_intelligence(project_id)
        if not intelligence:
            return {"error": "Project not analyzed"}
        
        try:
            viz_type = VisualizationType(visualization_type)
            return self.visualization_engine.generate_visualization(viz_type, intelligence, **kwargs)
        except ValueError:
            return {"error": f"Unknown visualization type: {visualization_type}"}
    
    def generate_project_dashboard(self, project_id: str) -> Dict[str, Any]:
        """Generate a comprehensive project dashboard."""
        intelligence = self.get_intelligence(project_id)
        if not intelligence:
            return {"error": "Project not analyzed"}
        
        return self.visualization_engine.generate_project_dashboard(intelligence)
    
    def export_visualization(self, visualization_data: Dict[str, Any], output_path: str, format: str = "html") -> bool:
        """Export a visualization to file."""
        return self.visualization_engine.export_visualization(visualization_data, output_path, format)
    
    def get_available_visualizations(self) -> List[str]:
        """Get list of available visualization types."""
        return self.visualization_engine.get_available_visualizations()
    
    def _build_project_structure(self, root_path: Path, project_name: str,
                                 file_analyses: Dict[str, UniversalFile]) -> Dict[str, Any]:
        """Build hierarchical project structure."""
        structure = {
            'name': project_name,
            'path': str(root_path),
            'type': ElementType.PROJECT.name,
            'children': {}
        }
        
        # Build tree structure
        for file_path, file_analysis in file_analyses.items():
            rel_path = Path(file_path).relative_to(root_path)
            parts = rel_path.parts
            
            current = structure['children']
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {
                        'name': part,
                        'type': ElementType.PACKAGE.name,
                        'children': {}
                    }
                current = current[part]['children']
            
            # Add file
            file_name = parts[-1]
            current[file_name] = {
                'name': file_name,
                'type': ElementType.FILE.name,
                'language': file_analysis.language.value,
                'metrics': {
                    'lines': file_analysis.total_lines,
                    'complexity': file_analysis.complexity,
                    'nodes': len(file_analysis.nodes)
                }
            }
        
        return structure
    
    def _calculate_enhanced_metrics(self, file_analyses: Dict[str, UniversalFile], 
                                  intelligence: CodeIntelligence) -> Dict[str, Any]:
        """Calculate enhanced project metrics including intelligence data."""
        total_lines = sum(f.total_lines for f in file_analyses.values())
        total_code_lines = sum(f.code_lines for f in file_analyses.values())
        total_nodes = sum(len(f.nodes) for f in file_analyses.values())
        complexities = [f.complexity for f in file_analyses.values() if f.complexity > 0]
        
        # Calculate symbol type distribution
        symbol_types = {}
        for symbol in intelligence.symbols.values():
            symbol_type = symbol.type.name
            symbol_types[symbol_type] = symbol_types.get(symbol_type, 0) + 1
        
        # Calculate relationship type distribution
        relationship_types = {}
        for rel in intelligence.relationships:
            rel_type = rel.type.value
            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
        
        # Calculate cognitive complexity metrics
        cognitive_complexities = [
            symbol.cognitive_complexity for symbol in intelligence.symbols.values()
            if hasattr(symbol, 'cognitive_complexity') and symbol.cognitive_complexity > 0
        ]
        
        return {
            # Basic metrics
            'total_files': len(file_analyses),
            'total_lines': total_lines,
            'total_code_lines': total_code_lines,
            'total_nodes': total_nodes,
            'average_complexity': sum(complexities) / len(complexities) if complexities else 0,
            'max_complexity': max(complexities) if complexities else 0,
            'total_imports': sum(len(f.imports) for f in file_analyses.values()),
            
            # Intelligence metrics
            'total_symbols': len(intelligence.symbols),
            'total_relationships': len(intelligence.relationships),
            'total_references': sum(len(refs) for refs in intelligence.references.values()),
            'symbol_types': symbol_types,
            'relationship_types': relationship_types,
            
            # Advanced complexity metrics
            'average_cognitive_complexity': sum(cognitive_complexities) / len(cognitive_complexities) if cognitive_complexities else 0,
            'max_cognitive_complexity': max(cognitive_complexities) if cognitive_complexities else 0,
            
            # Graph metrics (if available)
            'graph_metrics': intelligence.metrics.get('graph_metrics', {})
        }
    
    def _analyze_dependencies(self, file_analyses: Dict[str, UniversalFile]) -> Dict[str, List[str]]:
        """Build dependency graph from imports."""
        dependencies = {}
        
        for file_path, file_analysis in file_analyses.items():
            deps = []
            for import_stmt in file_analysis.imports:
                # Try to resolve import to local file
                resolved = self._resolve_import(import_stmt, file_path, file_analyses)
                if resolved:
                    deps.append(resolved)
            
            if deps:
                dependencies[file_path] = deps
        
        return dependencies
    
    def _resolve_import(self, import_stmt: str, from_file: str, 
                       all_files: Dict[str, UniversalFile]) -> Optional[str]:
        """Resolve import to local file if possible."""
        # Simple resolution - would need enhancement for real use
        module_name = import_stmt.split('.')[0]
        
        for file_path in all_files:
            if Path(file_path).stem == module_name:
                return file_path
        
        return None
    
    def _get_language_distribution(self, file_analyses: Dict[str, UniversalFile]) -> Dict[str, int]:
        """Get distribution of languages in project."""
        distribution = {}
        for file_analysis in file_analyses.values():
            lang = file_analysis.language.value
            distribution[lang] = distribution.get(lang, 0) + 1
        return distribution
