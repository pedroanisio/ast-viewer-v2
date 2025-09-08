"""Core visualization engine for code intelligence platform."""

import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from enum import Enum
import json

from ..models.universal import CodeIntelligence, UniversalFile, ElementType, RelationType

logger = logging.getLogger(__name__)


class VisualizationType(Enum):
    """Types of visualizations available."""
    # Graph visualizations
    DEPENDENCY_GRAPH = "dependency_graph"
    CALL_GRAPH = "call_graph"
    REFERENCE_NETWORK = "reference_network"
    INHERITANCE_TREE = "inheritance_tree"
    
    # Heat maps and matrices
    COMPLEXITY_HEATMAP = "complexity_heatmap"
    FILE_INTERACTION_MATRIX = "file_interaction_matrix"
    COUPLING_MATRIX = "coupling_matrix"
    
    # Architectural views
    ARCHITECTURE_MAP = "architecture_map"
    MODULE_OVERVIEW = "module_overview"
    LAYER_DIAGRAM = "layer_diagram"
    
    # Analysis views
    IMPACT_VISUALIZATION = "impact_visualization"
    CHANGE_PROPAGATION = "change_propagation"
    HOTSPOT_ANALYSIS = "hotspot_analysis"
    
    # Timeline and evolution
    EVOLUTION_TIMELINE = "evolution_timeline"
    GROWTH_ANALYSIS = "growth_analysis"
    
    # Interactive dashboards
    PROJECT_DASHBOARD = "project_dashboard"
    QUALITY_DASHBOARD = "quality_dashboard"


class VisualizationConfig:
    """Configuration for visualization rendering."""
    
    def __init__(self):
        # Layout settings
        self.width = 1200
        self.height = 800
        self.interactive = True
        
        # Graph settings
        self.node_size_range = (10, 50)
        self.edge_width_range = (1, 5)
        self.layout_algorithm = "force_directed"  # force_directed, hierarchical, circular
        
        # Color settings
        self.color_scheme = "viridis"
        self.background_color = "#ffffff"
        self.text_color = "#333333"
        
        # Filter settings
        self.min_complexity = 1
        self.max_depth = 5
        self.show_labels = True
        self.show_metrics = True
        
        # Export settings
        self.format = "html"  # html, png, svg, pdf, json
        self.quality = "high"
        
        # Performance settings
        self.max_nodes = 1000
        self.enable_clustering = True
        self.cluster_threshold = 100


class VisualizationEngine:
    """Main engine for generating code intelligence visualizations."""
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
        self.cache: Dict[str, Any] = {}
        
        # Import renderers dynamically
        self.renderers = {}
        self._initialize_renderers()
    
    def _initialize_renderers(self):
        """Initialize all available renderers."""
        try:
            from .renderers import (
                DependencyGraphRenderer,
                CallGraphRenderer,
                ComplexityHeatMapRenderer,
                ArchitectureMapRenderer,
                InteractiveGraphRenderer,
            )
            
            self.renderers = {
                VisualizationType.DEPENDENCY_GRAPH: DependencyGraphRenderer(self.config),
                VisualizationType.CALL_GRAPH: CallGraphRenderer(self.config),
                VisualizationType.COMPLEXITY_HEATMAP: ComplexityHeatMapRenderer(self.config),
                VisualizationType.ARCHITECTURE_MAP: ArchitectureMapRenderer(self.config),
                VisualizationType.REFERENCE_NETWORK: InteractiveGraphRenderer(self.config),
            }
            
            logger.info(f"Initialized {len(self.renderers)} visualization renderers")
            
        except ImportError as e:
            logger.warning(f"Some visualization renderers unavailable: {e}")
    
    def generate_visualization(self, 
                             visualization_type: VisualizationType,
                             intelligence: CodeIntelligence,
                             **kwargs) -> Dict[str, Any]:
        """Generate a visualization of the specified type."""
        
        logger.info(f"Generating {visualization_type.value} visualization")
        
        # Check cache
        cache_key = f"{visualization_type.value}_{hash(str(kwargs))}"
        if cache_key in self.cache:
            logger.debug(f"Returning cached visualization: {cache_key}")
            return self.cache[cache_key]
        
        # Get appropriate renderer
        renderer = self.renderers.get(visualization_type)
        if not renderer:
            return self._generate_fallback_visualization(visualization_type, intelligence, **kwargs)
        
        try:
            # Generate visualization
            result = renderer.render(intelligence, **kwargs)
            
            # Cache result
            self.cache[cache_key] = result
            
            logger.info(f"Successfully generated {visualization_type.value} visualization")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate {visualization_type.value}: {e}")
            return self._generate_error_visualization(str(e))
    
    def generate_project_dashboard(self, intelligence: CodeIntelligence) -> Dict[str, Any]:
        """Generate a comprehensive project dashboard with multiple visualizations."""
        
        logger.info("Generating comprehensive project dashboard")
        
        dashboard = {
            "type": "dashboard",
            "title": f"Project Dashboard - {intelligence.project_id}",
            "timestamp": self._get_timestamp(),
            "sections": []
        }
        
        # 1. Project Overview Section
        overview_section = {
            "title": "Project Overview",
            "visualizations": []
        }
        
        # Architecture map
        if VisualizationType.ARCHITECTURE_MAP in self.renderers:
            arch_viz = self.generate_visualization(
                VisualizationType.ARCHITECTURE_MAP, intelligence
            )
            overview_section["visualizations"].append(arch_viz)
        
        # Complexity heatmap
        if VisualizationType.COMPLEXITY_HEATMAP in self.renderers:
            complexity_viz = self.generate_visualization(
                VisualizationType.COMPLEXITY_HEATMAP, intelligence
            )
            overview_section["visualizations"].append(complexity_viz)
        
        dashboard["sections"].append(overview_section)
        
        # 2. Dependency Analysis Section
        dependency_section = {
            "title": "Dependency Analysis", 
            "visualizations": []
        }
        
        # Dependency graph
        if VisualizationType.DEPENDENCY_GRAPH in self.renderers:
            dep_viz = self.generate_visualization(
                VisualizationType.DEPENDENCY_GRAPH, intelligence
            )
            dependency_section["visualizations"].append(dep_viz)
        
        dashboard["sections"].append(dependency_section)
        
        # 3. Call Graph Analysis Section
        call_section = {
            "title": "Call Graph Analysis",
            "visualizations": []
        }
        
        # Call graph for top functions
        top_functions = self._get_top_functions_by_complexity(intelligence, limit=5)
        for func_id in top_functions:
            call_viz = self.generate_visualization(
                VisualizationType.CALL_GRAPH, intelligence, root_symbol=func_id
            )
            call_section["visualizations"].append(call_viz)
        
        dashboard["sections"].append(call_section)
        
        # 4. Summary metrics
        dashboard["metrics"] = self._extract_dashboard_metrics(intelligence)
        
        logger.info("Project dashboard generation complete")
        return dashboard
    
    def generate_custom_visualization(self, 
                                    data: Dict[str, Any],
                                    visualization_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a custom visualization from specification."""
        
        viz_type = visualization_spec.get("type", "graph")
        
        if viz_type == "graph":
            return self._generate_custom_graph(data, visualization_spec)
        elif viz_type == "heatmap":
            return self._generate_custom_heatmap(data, visualization_spec)
        elif viz_type == "dashboard":
            return self._generate_custom_dashboard(data, visualization_spec)
        else:
            return self._generate_error_visualization(f"Unknown visualization type: {viz_type}")
    
    def export_visualization(self, 
                           visualization: Dict[str, Any],
                           output_path: Union[str, Path],
                           format: str = "html") -> bool:
        """Export visualization to file."""
        
        try:
            from .exporters import VisualizationExporter
            
            exporter = VisualizationExporter()
            return exporter.export(visualization, output_path, format)
            
        except ImportError:
            logger.error("Visualization exporter not available")
            return False
        except Exception as e:
            logger.error(f"Failed to export visualization: {e}")
            return False
    
    def get_available_visualizations(self) -> List[str]:
        """Get list of available visualization types."""
        return [vt.value for vt in VisualizationType]
    
    def clear_cache(self):
        """Clear visualization cache."""
        self.cache.clear()
        logger.info("Visualization cache cleared")
    
    # Helper methods
    def _generate_fallback_visualization(self, 
                                       visualization_type: VisualizationType,
                                       intelligence: CodeIntelligence,
                                       **kwargs) -> Dict[str, Any]:
        """Generate a fallback visualization when renderer is not available."""
        
        return {
            "type": "fallback",
            "visualization_type": visualization_type.value,
            "message": f"Renderer for {visualization_type.value} not available",
            "data_summary": {
                "symbols": len(intelligence.symbols),
                "relationships": len(intelligence.relationships),
                "files": len(intelligence.files)
            },
            "suggestions": [
                "Install additional visualization dependencies",
                "Use alternative visualization type",
                "Check renderer configuration"
            ]
        }
    
    def _generate_error_visualization(self, error_message: str) -> Dict[str, Any]:
        """Generate an error visualization."""
        
        return {
            "type": "error",
            "message": error_message,
            "timestamp": self._get_timestamp()
        }
    
    def _get_top_functions_by_complexity(self, 
                                       intelligence: CodeIntelligence,
                                       limit: int = 10) -> List[str]:
        """Get top functions by complexity."""
        
        functions = [
            (symbol_id, symbol) for symbol_id, symbol in intelligence.symbols.items()
            if symbol.type in [ElementType.FUNCTION, ElementType.METHOD]
        ]
        
        # Sort by complexity
        functions.sort(key=lambda x: x[1].complexity, reverse=True)
        
        return [func_id for func_id, _ in functions[:limit]]
    
    def _extract_dashboard_metrics(self, intelligence: CodeIntelligence) -> Dict[str, Any]:
        """Extract key metrics for dashboard."""
        
        metrics = {
            "overview": {
                "total_symbols": len(intelligence.symbols),
                "total_files": len(intelligence.files),
                "total_relationships": len(intelligence.relationships),
                "total_references": sum(len(refs) for refs in intelligence.references.values())
            },
            "complexity": {},
            "relationships": {},
            "quality": {}
        }
        
        # Complexity metrics
        complexities = [s.complexity for s in intelligence.symbols.values() if s.complexity > 0]
        if complexities:
            metrics["complexity"] = {
                "average": sum(complexities) / len(complexities),
                "max": max(complexities),
                "total_high_complexity": len([c for c in complexities if c > 10])
            }
        
        # Relationship metrics
        rel_types = {}
        for rel in intelligence.relationships:
            rel_type = rel.type.value
            rel_types[rel_type] = rel_types.get(rel_type, 0) + 1
        metrics["relationships"] = rel_types
        
        # Graph metrics
        if intelligence.dependency_graph:
            metrics["graph"] = {
                "density": intelligence.dependency_graph.density,
                "cycles": len(intelligence.dependency_graph.cycles),
                "components": intelligence.dependency_graph.strongly_connected_components
            }
        
        return metrics
    
    def _generate_custom_graph(self, data: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate custom graph visualization."""
        # Implementation for custom graph generation
        return {"type": "custom_graph", "spec": spec, "data": data}
    
    def _generate_custom_heatmap(self, data: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate custom heatmap visualization."""
        # Implementation for custom heatmap generation
        return {"type": "custom_heatmap", "spec": spec, "data": data}
    
    def _generate_custom_dashboard(self, data: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate custom dashboard visualization."""
        # Implementation for custom dashboard generation
        return {"type": "custom_dashboard", "spec": spec, "data": data}
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
