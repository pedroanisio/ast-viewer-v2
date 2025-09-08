"""Export utilities for visualization data."""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class VisualizationExporter:
    """Export visualizations to various formats."""
    
    def __init__(self):
        self.supported_formats = ['html', 'json', 'png', 'svg', 'pdf']
    
    def export(self, 
               visualization: Dict[str, Any], 
               output_path: Union[str, Path],
               format: str = 'html') -> bool:
        """Export visualization to specified format."""
        
        output_path = Path(output_path)
        
        if format not in self.supported_formats:
            logger.error(f"Unsupported format: {format}")
            return False
        
        try:
            if format == 'html':
                return self._export_html(visualization, output_path)
            elif format == 'json':
                return self._export_json(visualization, output_path)
            elif format == 'png':
                return self._export_image(visualization, output_path, 'png')
            elif format == 'svg':
                return self._export_image(visualization, output_path, 'svg')
            elif format == 'pdf':
                return self._export_pdf(visualization, output_path)
            
        except Exception as e:
            logger.error(f"Failed to export visualization: {e}")
            return False
        
        return False
    
    def _export_html(self, visualization: Dict[str, Any], output_path: Path) -> bool:
        """Export as interactive HTML."""
        
        if visualization.get('format') == 'plotly':
            return self._export_plotly_html(visualization, output_path)
        else:
            return self._export_generic_html(visualization, output_path)
    
    def _export_plotly_html(self, visualization: Dict[str, Any], output_path: Path) -> bool:
        """Export Plotly visualization as HTML."""
        
        try:
            import plotly.graph_objects as go
            
            # Reconstruct Plotly figure from JSON
            fig_data = visualization.get('data', {})
            fig = go.Figure(fig_data)
            
            # Write HTML file
            fig.write_html(str(output_path), 
                          include_plotlyjs='cdn',
                          config={'displayModeBar': True})
            
            logger.info(f"Exported Plotly visualization to {output_path}")
            return True
            
        except ImportError:
            logger.error("Plotly not available for HTML export")
            return False
        except Exception as e:
            logger.error(f"Failed to export Plotly HTML: {e}")
            return False
    
    def _export_generic_html(self, visualization: Dict[str, Any], output_path: Path) -> bool:
        """Export generic visualization as HTML."""
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .content {{ margin-top: 20px; }}
                .metadata {{ background: #e8f4f8; padding: 15px; border-radius: 5px; margin-top: 20px; }}
                .error {{ color: red; background: #ffe6e6; padding: 10px; border-radius: 5px; }}
                pre {{ background: #f8f8f8; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
                <p>Generated on: {timestamp}</p>
            </div>
            
            <div class="content">
                {content}
            </div>
            
            {metadata_section}
        </body>
        </html>
        """
        
        title = visualization.get('title', 'Code Visualization')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Generate content based on visualization type
        if 'error' in visualization:
            content = f'<div class="error">Error: {visualization["error"]}</div>'
        else:
            content = f'<pre>{json.dumps(visualization.get("data", {}), indent=2)}</pre>'
        
        # Generate metadata section
        metadata = visualization.get('metadata', {})
        metadata_html = ""
        if metadata:
            metadata_html = '<div class="metadata"><h3>Metadata</h3>'
            for key, value in metadata.items():
                metadata_html += f'<p><strong>{key}:</strong> {value}</p>'
            metadata_html += '</div>'
        
        # Fill template
        html_content = html_template.format(
            title=title,
            timestamp=timestamp,
            content=content,
            metadata_section=metadata_html
        )
        
        # Write file
        output_path.write_text(html_content, encoding='utf-8')
        logger.info(f"Exported generic HTML to {output_path}")
        return True
    
    def _export_json(self, visualization: Dict[str, Any], output_path: Path) -> bool:
        """Export as JSON."""
        
        try:
            # Add export metadata
            export_data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'format': 'json',
                    'version': '1.0'
                },
                'visualization': visualization
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported JSON to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            return False
    
    def _export_image(self, visualization: Dict[str, Any], output_path: Path, format: str) -> bool:
        """Export as image (PNG/SVG)."""
        
        if visualization.get('format') == 'plotly':
            return self._export_plotly_image(visualization, output_path, format)
        else:
            logger.warning("Image export only supported for Plotly visualizations")
            return False
    
    def _export_plotly_image(self, visualization: Dict[str, Any], output_path: Path, format: str) -> bool:
        """Export Plotly visualization as image."""
        
        try:
            import plotly.graph_objects as go
            
            # Reconstruct figure
            fig_data = visualization.get('data', {})
            fig = go.Figure(fig_data)
            
            # Export image
            if format == 'png':
                fig.write_image(str(output_path), format='png', width=1200, height=800)
            elif format == 'svg':
                fig.write_image(str(output_path), format='svg', width=1200, height=800)
            
            logger.info(f"Exported {format.upper()} image to {output_path}")
            return True
            
        except ImportError:
            logger.error("Plotly and/or kaleido not available for image export")
            return False
        except Exception as e:
            logger.error(f"Failed to export {format} image: {e}")
            return False
    
    def _export_pdf(self, visualization: Dict[str, Any], output_path: Path) -> bool:
        """Export as PDF."""
        
        try:
            # First export as HTML, then convert to PDF
            html_path = output_path.with_suffix('.html')
            
            if self._export_html(visualization, html_path):
                # Try to convert HTML to PDF using weasyprint or similar
                try:
                    import weasyprint
                    html_doc = weasyprint.HTML(filename=str(html_path))
                    html_doc.write_pdf(str(output_path))
                    
                    # Clean up temporary HTML
                    html_path.unlink()
                    
                    logger.info(f"Exported PDF to {output_path}")
                    return True
                    
                except ImportError:
                    logger.warning("WeasyPrint not available for PDF export. HTML file created instead.")
                    return False
            
        except Exception as e:
            logger.error(f"Failed to export PDF: {e}")
            return False
        
        return False
    
    def batch_export(self, 
                     visualizations: Dict[str, Dict[str, Any]],
                     output_dir: Union[str, Path],
                     formats: list = None) -> Dict[str, bool]:
        """Export multiple visualizations."""
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        formats = formats or ['html', 'json']
        results = {}
        
        for viz_name, viz_data in visualizations.items():
            viz_results = {}
            
            for format in formats:
                output_path = output_dir / f"{viz_name}.{format}"
                success = self.export(viz_data, output_path, format)
                viz_results[format] = success
            
            results[viz_name] = viz_results
        
        return results
    
    def create_dashboard_export(self, 
                              dashboard: Dict[str, Any],
                              output_path: Union[str, Path]) -> bool:
        """Export complete dashboard as multi-file HTML."""
        
        output_path = Path(output_path)
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Create main dashboard HTML
            dashboard_html = self._create_dashboard_html(dashboard)
            
            # Write main file
            output_path.write_text(dashboard_html, encoding='utf-8')
            
            # Export individual visualizations
            viz_dir = output_path.parent / (output_path.stem + '_visualizations')
            viz_dir.mkdir(exist_ok=True)
            
            for section in dashboard.get('sections', []):
                for i, viz in enumerate(section.get('visualizations', [])):
                    viz_name = f"{section['title'].lower().replace(' ', '_')}_{i}"
                    viz_path = viz_dir / f"{viz_name}.html"
                    self.export(viz, viz_path, 'html')
            
            logger.info(f"Exported dashboard to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export dashboard: {e}")
            return False
    
    def _create_dashboard_html(self, dashboard: Dict[str, Any]) -> str:
        """Create HTML for dashboard."""
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .dashboard {{ max-width: 1400px; margin: 0 auto; }}
                .header {{ background: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .section {{ background: white; margin-bottom: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .section-header {{ background: #3498db; color: white; padding: 15px 30px; border-radius: 10px 10px 0 0; }}
                .section-content {{ padding: 20px 30px; }}
                .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
                .metric {{ background: #ecf0f1; padding: 15px; border-radius: 5px; text-align: center; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
                .metric-label {{ font-size: 14px; color: #7f8c8d; }}
                .visualization {{ margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="dashboard">
                <div class="header">
                    <h1>{title}</h1>
                    <p>Generated on: {timestamp}</p>
                    {metrics_html}
                </div>
                
                {sections_html}
            </div>
        </body>
        </html>
        """
        
        title = dashboard.get('title', 'Code Intelligence Dashboard')
        timestamp = dashboard.get('timestamp', datetime.now().isoformat())
        
        # Create metrics HTML
        metrics = dashboard.get('metrics', {})
        metrics_html = ""
        if metrics:
            metrics_html = '<div class="metrics">'
            
            # Overview metrics
            overview = metrics.get('overview', {})
            for key, value in overview.items():
                label = key.replace('_', ' ').title()
                metrics_html += f'''
                <div class="metric">
                    <div class="metric-value">{value:,}</div>
                    <div class="metric-label">{label}</div>
                </div>
                '''
            
            metrics_html += '</div>'
        
        # Create sections HTML
        sections_html = ""
        for section in dashboard.get('sections', []):
            section_title = section.get('title', 'Section')
            
            sections_html += f'''
            <div class="section">
                <div class="section-header">
                    <h2>{section_title}</h2>
                </div>
                <div class="section-content">
            '''
            
            # Add visualizations
            for viz in section.get('visualizations', []):
                viz_title = viz.get('title', 'Visualization')
                sections_html += f'''
                <div class="visualization">
                    <h3>{viz_title}</h3>
                    <p>Visualization data available in exported files.</p>
                </div>
                '''
            
            sections_html += '</div></div>'
        
        return html_template.format(
            title=title,
            timestamp=timestamp,
            metrics_html=metrics_html,
            sections_html=sections_html
        )
