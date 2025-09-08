"""Specialized renderers for different visualization types."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from abc import ABC, abstractmethod
import json
import math

try:
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import seaborn as sns
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import numpy as np
    import pandas as pd
except ImportError as e:
    logging.warning(f"Some visualization dependencies not available: {e}")
    # Create mock objects to prevent import errors
    nx = None
    plt = None
    sns = None
    go = None
    px = None
    np = None
    pd = None

from ..models.universal import CodeIntelligence, ElementType, RelationType

logger = logging.getLogger(__name__)


class BaseRenderer(ABC):
    """Base class for visualization renderers."""
    
    def __init__(self, config):
        self.config = config
    
    @abstractmethod
    def render(self, intelligence: CodeIntelligence, **kwargs) -> Dict[str, Any]:
        """Render the visualization."""
        pass
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        return all([nx, plt, sns, go, px, np, pd])


class DependencyGraphRenderer(BaseRenderer):
    """Renderer for dependency graph visualizations."""
    
    def render(self, intelligence: CodeIntelligence, **kwargs) -> Dict[str, Any]:
        """Render dependency graph visualization."""
        
        if not self._check_dependencies():
            return {"error": "Visualization dependencies not available"}
        
        try:
            # Create NetworkX graph
            G = nx.DiGraph()
            
            # Add nodes (symbols)
            for symbol_id, symbol in intelligence.symbols.items():
                G.add_node(symbol_id, 
                          name=symbol.name or "unknown",
                          type=symbol.type.name,
                          complexity=symbol.complexity,
                          file=symbol.location.file_path)
            
            # Add edges (relationships)
            for rel in intelligence.relationships:
                if rel.type in [RelationType.CALLS, RelationType.USES, RelationType.IMPORTS, 
                               RelationType.EXTENDS, RelationType.IMPLEMENTS]:
                    G.add_edge(rel.source_id, rel.target_id, 
                              relation=rel.type.value,
                              confidence=rel.confidence)
            
            # Generate layout
            layout = self._generate_layout(G, kwargs.get('layout', 'spring'))
            
            # Create Plotly visualization
            fig = self._create_plotly_graph(G, layout, "Dependency Graph")
            
            # Convert to JSON for web display
            graph_json = fig.to_json()
            
            return {
                "type": "dependency_graph",
                "title": "Code Dependency Graph",
                "data": json.loads(graph_json),
                "metadata": {
                    "nodes": len(G.nodes()),
                    "edges": len(G.edges()),
                    "density": nx.density(G),
                    "is_connected": nx.is_weakly_connected(G)
                },
                "interactive": True,
                "format": "plotly"
            }
            
        except Exception as e:
            logger.error(f"Failed to render dependency graph: {e}")
            return {"error": str(e)}
    
    def _generate_layout(self, G: Any, layout_type: str) -> Dict[str, Tuple[float, float]]:
        """Generate node positions using specified layout algorithm."""
        
        if layout_type == "spring":
            return nx.spring_layout(G, k=1, iterations=50)
        elif layout_type == "circular":
            return nx.circular_layout(G)
        elif layout_type == "hierarchical":
            return nx.nx_agraph.graphviz_layout(G, prog='dot') if hasattr(nx, 'nx_agraph') else nx.spring_layout(G)
        else:
            return nx.spring_layout(G)
    
    def _create_plotly_graph(self, G: Any, layout: Dict, title: str) -> Any:
        """Create Plotly graph object."""
        
        # Extract node positions
        node_x = [layout[node][0] for node in G.nodes()]
        node_y = [layout[node][1] for node in G.nodes()]
        
        # Create edge traces
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = layout[edge[0]]
            x1, y1 = layout[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # Create edge trace
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Create node trace
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=[G.nodes[node].get('name', node[:8]) for node in G.nodes()],
            textposition="middle center",
            marker=dict(
                size=[min(50, max(10, G.nodes[node].get('complexity', 1) * 5)) for node in G.nodes()],
                color=[self._get_node_color(G.nodes[node].get('type', 'UNKNOWN')) for node in G.nodes()],
                line=dict(width=2, color='white')
            )
        )
        
        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title=title,
                           titlefont_size=16,
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Interactive dependency graph - hover for details",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002,
                               xanchor='left', yanchor='bottom',
                               font=dict(color='#888', size=12)
                           )],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                       ))
        
        return fig
    
    def _get_node_color(self, node_type: str) -> str:
        """Get color for node based on type."""
        colors = {
            'CLASS': '#FF6B6B',
            'FUNCTION': '#4ECDC4',
            'METHOD': '#45B7D1', 
            'VARIABLE': '#96CEB4',
            'IMPORT': '#FFEAA7',
            'INTERFACE': '#DDA0DD',
            'STRUCT': '#98D8C8',
            'ENUM': '#F7DC6F'
        }
        return colors.get(node_type, '#BDC3C7')


class CallGraphRenderer(BaseRenderer):
    """Renderer for call graph visualizations."""
    
    def render(self, intelligence: CodeIntelligence, **kwargs) -> Dict[str, Any]:
        """Render call graph visualization."""
        
        if not self._check_dependencies():
            return {"error": "Visualization dependencies not available"}
        
        root_symbol = kwargs.get('root_symbol')
        max_depth = kwargs.get('max_depth', 3)
        
        if not root_symbol or root_symbol not in intelligence.symbols:
            return {"error": "Root symbol not found or not specified"}
        
        try:
            # Build call graph starting from root symbol
            call_graph = self._build_call_subgraph(intelligence, root_symbol, max_depth)
            
            # Create hierarchical layout
            layout = self._create_hierarchical_layout(call_graph)
            
            # Create Plotly visualization
            fig = self._create_call_graph_plot(call_graph, layout, intelligence.symbols[root_symbol].name)
            
            return {
                "type": "call_graph",
                "title": f"Call Graph - {intelligence.symbols[root_symbol].name}",
                "data": json.loads(fig.to_json()),
                "metadata": {
                    "root_symbol": root_symbol,
                    "max_depth": max_depth,
                    "nodes": len(call_graph.nodes()),
                    "edges": len(call_graph.edges())
                },
                "interactive": True,
                "format": "plotly"
            }
            
        except Exception as e:
            logger.error(f"Failed to render call graph: {e}")
            return {"error": str(e)}
    
    def _build_call_subgraph(self, intelligence: CodeIntelligence, root_symbol: str, max_depth: int) -> Any:
        """Build call subgraph starting from root symbol."""
        
        G = nx.DiGraph()
        visited = set()
        queue = [(root_symbol, 0)]
        
        while queue:
            symbol_id, depth = queue.pop(0)
            
            if depth > max_depth or symbol_id in visited:
                continue
            
            visited.add(symbol_id)
            symbol = intelligence.symbols.get(symbol_id)
            
            if symbol:
                G.add_node(symbol_id,
                          name=symbol.name or "unknown",
                          type=symbol.type.name,
                          complexity=symbol.complexity,
                          depth=depth)
                
                # Find outgoing calls
                for rel in intelligence.relationships:
                    if rel.source_id == symbol_id and rel.type == RelationType.CALLS:
                        target_symbol = intelligence.symbols.get(rel.target_id)
                        if target_symbol:
                            G.add_edge(symbol_id, rel.target_id, relation='calls')
                            queue.append((rel.target_id, depth + 1))
        
        return G
    
    def _create_hierarchical_layout(self, G: Any) -> Dict[str, Tuple[float, float]]:
        """Create hierarchical layout for call graph."""
        
        layout = {}
        depth_groups = {}
        
        # Group nodes by depth
        for node in G.nodes():
            depth = G.nodes[node].get('depth', 0)
            if depth not in depth_groups:
                depth_groups[depth] = []
            depth_groups[depth].append(node)
        
        # Position nodes
        for depth, nodes in depth_groups.items():
            y = -depth * 2  # Vertical spacing
            for i, node in enumerate(nodes):
                x = (i - len(nodes)/2) * 3  # Horizontal spacing
                layout[node] = (x, y)
        
        return layout
    
    def _create_call_graph_plot(self, G: Any, layout: Dict, root_name: str) -> Any:
        """Create Plotly call graph visualization."""
        
        # Similar to dependency graph but with hierarchical styling
        return self._create_plotly_graph(G, layout, f"Call Graph - {root_name}")


class ComplexityHeatMapRenderer(BaseRenderer):
    """Renderer for complexity heat map visualizations."""
    
    def render(self, intelligence: CodeIntelligence, **kwargs) -> Dict[str, Any]:
        """Render complexity heat map visualization."""
        
        if not self._check_dependencies():
            return {"error": "Visualization dependencies not available"}
        
        try:
            # Prepare data for heat map
            heatmap_data = self._prepare_heatmap_data(intelligence)
            
            # Create Plotly heatmap
            fig = self._create_complexity_heatmap(heatmap_data)
            
            return {
                "type": "complexity_heatmap",
                "title": "Code Complexity Heat Map",
                "data": json.loads(fig.to_json()),
                "metadata": {
                    "files_analyzed": len(heatmap_data),
                    "avg_complexity": np.mean([d['complexity'] for d in heatmap_data]) if heatmap_data else 0
                },
                "interactive": True,
                "format": "plotly"
            }
            
        except Exception as e:
            logger.error(f"Failed to render complexity heatmap: {e}")
            return {"error": str(e)}
    
    def _prepare_heatmap_data(self, intelligence: CodeIntelligence) -> List[Dict[str, Any]]:
        """Prepare data for complexity heatmap."""
        
        file_complexity = {}
        
        # Aggregate complexity by file
        for symbol in intelligence.symbols.values():
            file_path = symbol.location.file_path
            if file_path not in file_complexity:
                file_complexity[file_path] = {
                    'total_complexity': 0,
                    'symbol_count': 0,
                    'max_complexity': 0,
                    'symbols': []
                }
            
            file_complexity[file_path]['total_complexity'] += symbol.complexity
            file_complexity[file_path]['symbol_count'] += 1
            file_complexity[file_path]['max_complexity'] = max(
                file_complexity[file_path]['max_complexity'], 
                symbol.complexity
            )
            file_complexity[file_path]['symbols'].append({
                'name': symbol.name,
                'type': symbol.type.name,
                'complexity': symbol.complexity,
                'line': symbol.location.start_line
            })
        
        # Convert to list format
        heatmap_data = []
        for file_path, data in file_complexity.items():
            avg_complexity = data['total_complexity'] / data['symbol_count'] if data['symbol_count'] > 0 else 0
            heatmap_data.append({
                'file': file_path,
                'complexity': avg_complexity,
                'max_complexity': data['max_complexity'],
                'symbol_count': data['symbol_count'],
                'symbols': data['symbols']
            })
        
        return sorted(heatmap_data, key=lambda x: x['complexity'], reverse=True)
    
    def _create_complexity_heatmap(self, data: List[Dict[str, Any]]) -> Any:
        """Create Plotly complexity heatmap."""
        
        if not data:
            return go.Figure()
        
        # Prepare data for heatmap
        files = [d['file'] for d in data]
        complexities = [d['complexity'] for d in data]
        symbol_counts = [d['symbol_count'] for d in data]
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=[complexities],
            x=files,
            y=['Complexity'],
            colorscale='Viridis',
            hoverongaps=False,
            hovertemplate='File: %{x}<br>Complexity: %{z}<br>Symbols: %{customdata}<extra></extra>',
            customdata=[symbol_counts]
        ))
        
        fig.update_layout(
            title="File Complexity Heat Map",
            xaxis_title="Files",
            yaxis_title="",
            height=200 + len(files) * 20,
            margin=dict(l=100, r=50, t=50, b=100)
        )
        
        return fig


class ArchitectureMapRenderer(BaseRenderer):
    """Renderer for architecture map visualizations."""
    
    def render(self, intelligence: CodeIntelligence, **kwargs) -> Dict[str, Any]:
        """Render architecture map visualization."""
        
        if not self._check_dependencies():
            return {"error": "Visualization dependencies not available"}
        
        try:
            # Analyze architectural components
            architecture_data = self._analyze_architecture(intelligence)
            
            # Create architecture visualization
            fig = self._create_architecture_map(architecture_data)
            
            return {
                "type": "architecture_map",
                "title": "Project Architecture Map",
                "data": json.loads(fig.to_json()),
                "metadata": architecture_data['metadata'],
                "interactive": True,
                "format": "plotly"
            }
            
        except Exception as e:
            logger.error(f"Failed to render architecture map: {e}")
            return {"error": str(e)}
    
    def _analyze_architecture(self, intelligence: CodeIntelligence) -> Dict[str, Any]:
        """Analyze project architecture."""
        
        # Group symbols by module/package
        modules = {}
        for symbol in intelligence.symbols.values():
            # Extract module from file path
            parts = symbol.location.file_path.split('/')
            module = '/'.join(parts[:-1]) if len(parts) > 1 else 'root'
            
            if module not in modules:
                modules[module] = {
                    'classes': 0,
                    'functions': 0,
                    'total_complexity': 0,
                    'files': set()
                }
            
            modules[module]['files'].add(symbol.location.file_path)
            modules[module]['total_complexity'] += symbol.complexity
            
            if symbol.type == ElementType.CLASS:
                modules[module]['classes'] += 1
            elif symbol.type in [ElementType.FUNCTION, ElementType.METHOD]:
                modules[module]['functions'] += 1
        
        # Convert sets to counts
        for module_data in modules.values():
            module_data['files'] = len(module_data['files'])
        
        return {
            'modules': modules,
            'metadata': {
                'total_modules': len(modules),
                'total_files': sum(m['files'] for m in modules.values()),
                'avg_complexity_per_module': sum(m['total_complexity'] for m in modules.values()) / len(modules) if modules else 0
            }
        }
    
    def _create_architecture_map(self, architecture_data: Dict[str, Any]) -> Any:
        """Create architecture map visualization."""
        
        modules = architecture_data['modules']
        
        # Create treemap
        labels = list(modules.keys())
        values = [m['total_complexity'] for m in modules.values()]
        parents = [''] * len(labels)  # All modules at root level for now
        
        fig = go.Figure(go.Treemap(
            labels=labels,
            values=values,
            parents=parents,
            textinfo="label+value",
            hovertemplate='<b>%{label}</b><br>Complexity: %{value}<br>Classes: %{customdata[0]}<br>Functions: %{customdata[1]}<br>Files: %{customdata[2]}<extra></extra>',
            customdata=[[m['classes'], m['functions'], m['files']] for m in modules.values()]
        ))
        
        fig.update_layout(
            title="Project Architecture Map (by Module Complexity)",
            margin=dict(t=50, l=25, r=25, b=25)
        )
        
        return fig


class InteractiveGraphRenderer(BaseRenderer):
    """Renderer for interactive graph visualizations."""
    
    def render(self, intelligence: CodeIntelligence, **kwargs) -> Dict[str, Any]:
        """Render interactive graph visualization."""
        
        # This can be used for reference networks, custom graphs, etc.
        visualization_type = kwargs.get('graph_type', 'reference_network')
        
        if visualization_type == 'reference_network':
            return self._render_reference_network(intelligence, **kwargs)
        else:
            return {"error": f"Unknown graph type: {visualization_type}"}
    
    def _render_reference_network(self, intelligence: CodeIntelligence, **kwargs) -> Dict[str, Any]:
        """Render reference network visualization."""
        
        if not self._check_dependencies():
            return {"error": "Visualization dependencies not available"}
        
        try:
            # Create reference network graph
            G = nx.Graph()  # Undirected for reference network
            
            # Add symbols as nodes
            for symbol_id, symbol in intelligence.symbols.items():
                ref_count = len(intelligence.get_symbol_references(symbol_id))
                G.add_node(symbol_id,
                          name=symbol.name or "unknown",
                          type=symbol.type.name,
                          references=ref_count,
                          complexity=symbol.complexity)
            
            # Add edges based on references
            for symbol_id, references in intelligence.references.items():
                for ref in references:
                    # Find which symbol contains this reference
                    for other_id, other_symbol in intelligence.symbols.items():
                        if (other_symbol.location.file_path == ref.location.file_path and
                            other_symbol.location.start_line <= ref.location.start_line <= other_symbol.location.end_line):
                            if symbol_id != other_id:
                                G.add_edge(symbol_id, other_id, weight=1)
                            break
            
            # Generate layout
            layout = nx.spring_layout(G, k=2, iterations=50)
            
            # Create visualization
            fig = self._create_plotly_graph(G, layout, "Reference Network")
            
            return {
                "type": "reference_network", 
                "title": "Symbol Reference Network",
                "data": json.loads(fig.to_json()),
                "metadata": {
                    "nodes": len(G.nodes()),
                    "edges": len(G.edges()),
                    "density": nx.density(G)
                },
                "interactive": True,
                "format": "plotly"
            }
            
        except Exception as e:
            logger.error(f"Failed to render reference network: {e}")
            return {"error": str(e)}
