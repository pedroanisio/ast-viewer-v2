"""Modern GraphQL schema implementing Strawberry best practices."""

from typing import List, Optional, Union
from pathlib import Path
import strawberry
import logging

# Import types from the new modular structure
from .types import (
    UniversalFileType, AnalysisResult, ProjectMetrics, 
    IntelligenceData, SourceLocationType, UniversalNodeType,
    RelationshipType, ReferenceType, ElementTypeEnum, LanguageEnum
)

# Import new components
from .context import Context
from .errors import (
    FileNotFoundError, DirectoryNotFoundError,
    AnalysisError, ValidationError, InternalError
)
from .inputs import (
    FileAnalysisInput, DirectoryAnalysisInput, ProjectAnalysisInput,
    SymbolSearchInput, RelationshipFilterInput, VisualizationInput,
    ImpactAnalysisInput, CodeMetricsInput
)
from ..common.converters import convert_nodes_to_graphql

logger = logging.getLogger(__name__)


@strawberry.type
class UniversalNodeTypeEnhanced:
    """Enhanced Universal Node with field resolvers."""
    id: str
    type: ElementTypeEnum
    name: Optional[str]
    language: LanguageEnum
    
    # Private fields for internal use
    _source_data: strawberry.Private[dict]
    
    @strawberry.field
    def display_name(self) -> str:
        """Computed display name for the node."""
        if self.name:
            return f"{self.name} ({self.type.value})"
        return f"<{self.type.value}>"
    
    @strawberry.field
    async def related_symbols(self, info: strawberry.Info, limit: int = 10) -> List["UniversalNodeTypeEnhanced"]:
        """Get related symbols using DataLoader."""
        context: Context = info.context
        try:
            relationships = await context.dataloaders.relationships_loader.load(self.id)
            # Convert relationships to symbols (simplified)
            related_ids = [rel.get("target_id") for rel in relationships[:limit]]
            related_symbols = await context.dataloaders.symbol_loader.load_many(related_ids)
            return [self._convert_to_enhanced(symbol) for symbol in related_symbols if symbol]
        except Exception as e:
            logger.warning(f"Failed to load related symbols for {self.id}: {e}")
            return []
    
    @strawberry.field
    async def references_count(self, info: strawberry.Info) -> int:
        """Get count of references to this symbol."""
        context: Context = info.context
        try:
            references = await context.dataloaders.references_loader.load(self.id)
            return len(references)
        except Exception:
            return 0
    
    @strawberry.field
    def complexity_level(self) -> str:
        """Human-readable complexity level."""
        complexity = self._source_data.get("complexity", 1)
        if complexity <= 5:
            return "Low"
        elif complexity <= 10:
            return "Medium"
        elif complexity <= 20:
            return "High"
        else:
            return "Very High"
    
    @classmethod
    def _convert_to_enhanced(cls, data: dict) -> "UniversalNodeTypeEnhanced":
        """Convert raw data to enhanced type."""
        return cls(
            id=data.get("id", ""),
            type=ElementTypeEnum(data.get("type", "UNKNOWN")),
            name=data.get("name"),
            language=LanguageEnum(data.get("language", "UNKNOWN")),
            _source_data=data
        )


@strawberry.type
class Query:
    """Modern GraphQL Query with best practices."""
    
    @strawberry.field
    async def analyze_file(
        self, 
        info: strawberry.Info, 
        input: FileAnalysisInput
    ) -> Union[UniversalFileType, FileNotFoundError, AnalysisError, ValidationError]:
        """Analyze a single file with proper error handling."""
        context: Context = info.context
        
        # Validate input
        if not input.file_path:
            return ValidationError(field="file_path", message="File path is required")
        
        try:
            file_path = Path(input.file_path)
            
            # Check if file exists
            if not file_path.exists():
                return FileNotFoundError(input.file_path)
            
            # Use analyzer from context
            result = context.universal_analyzer.analyze_file(file_path)
            
            if not result:
                return AnalysisError(input.file_path, Exception("Analysis returned no results"))
            
            # Convert to GraphQL types
            nodes = convert_nodes_to_graphql(result.nodes)
            
            return UniversalFileType(
                path=result.path,
                language=LanguageEnum(result.language.value),
                encoding=result.encoding,
                size_bytes=result.size_bytes,
                hash=result.hash,
                total_lines=result.total_lines,
                code_lines=result.code_lines,
                comment_lines=result.comment_lines,
                blank_lines=result.blank_lines,
                nodes=nodes,
                imports=result.imports,
                exports=result.exports,
                complexity=result.complexity,
                maintainability_index=result.maintainability_index
            )
            
        except FileNotFoundError:
            return FileNotFoundError(input.file_path)
        except Exception as e:
            logger.error(f"File analysis failed for {input.file_path}: {e}")
            return AnalysisError(input.file_path, e)
    
    @strawberry.field
    async def analyze_directory(
        self, 
        info: strawberry.Info, 
        input: DirectoryAnalysisInput
    ) -> Union[AnalysisResult, DirectoryNotFoundError, AnalysisError, ValidationError]:
        """Analyze directory with structured input and error handling."""
        context: Context = info.context
        
        # Validate input
        if not input.directory_path:
            return ValidationError(field="directory_path", message="Directory path is required")
        
        try:
            directory_path = Path(input.directory_path)
            
            # Check if directory exists
            if not directory_path.exists():
                return DirectoryNotFoundError(input.directory_path)
            
            if not directory_path.is_dir():
                return ValidationError(field="directory_path", message="Path is not a directory")
            
            # Use analyzer from context
            results = context.universal_analyzer.analyze_directory(directory_path)
            
            if not results:
                return AnalysisError(input.directory_path, Exception("No files found to analyze"))
            
            # Convert results (similar to original but with error handling)
            files = []
            for file_result in results.values():
                nodes = convert_nodes_to_graphql(file_result.nodes)
                files.append(UniversalFileType(
                    path=file_result.path,
                    language=LanguageEnum(file_result.language.value),
                    encoding=file_result.encoding,
                    size_bytes=file_result.size_bytes,
                    hash=file_result.hash,
                    total_lines=file_result.total_lines,
                    code_lines=file_result.code_lines,
                    comment_lines=file_result.comment_lines,
                    blank_lines=file_result.blank_lines,
                    nodes=nodes,
                    imports=file_result.imports,
                    exports=file_result.exports,
                    complexity=file_result.complexity,
                    maintainability_index=file_result.maintainability_index
                ))
            
            # Calculate metrics
            total_lines = sum(f.total_lines for f in results.values())
            total_code_lines = sum(f.code_lines for f in results.values())
            total_nodes = sum(len(f.nodes) for f in results.values())
            complexities = [f.complexity for f in results.values() if f.complexity > 0]
            
            metrics = ProjectMetrics(
                total_files=len(results),
                total_lines=total_lines,
                total_code_lines=total_code_lines,
                total_nodes=total_nodes,
                average_complexity=sum(complexities) / len(complexities) if complexities else 0,
                max_complexity=max(complexities) if complexities else 0,
                total_imports=sum(len(f.imports) for f in results.values())
            )
            
            # Get language distribution
            language_dist = {}
            for file_result in results.values():
                lang = file_result.language.value
                language_dist[lang] = language_dist.get(lang, 0) + 1
            
            return AnalysisResult(
                files=files,
                metrics=metrics,
                languages=list(language_dist.keys())
            )
            
        except Exception as e:
            logger.error(f"Directory analysis failed for {input.directory_path}: {e}")
            return AnalysisError(input.directory_path, e)
    
    @strawberry.field
    async def analyze_project(
        self, 
        info: strawberry.Info, 
        input: ProjectAnalysisInput
    ) -> Union[AnalysisResult, DirectoryNotFoundError, AnalysisError, ValidationError]:
        """Comprehensive project analysis with intelligence."""
        context: Context = info.context
        
        try:
            directory_path = Path(input.directory_path)
            
            if not directory_path.exists():
                return DirectoryNotFoundError(input.directory_path)
            
            # Use integrated analyzer for full intelligence
            result = context.integrated_analyzer.analyze_project(
                directory_path, 
                input.project_name
            )
            
            if not result:
                return AnalysisError(input.directory_path, Exception("Project analysis failed"))
            
            # Convert to GraphQL result (implementation depends on result structure)
            # This would be expanded based on the actual IntegratedCodeAnalyzer output
            
            return AnalysisResult(
                files=[],  # Would be populated from result
                metrics=ProjectMetrics(
                    total_files=0,
                    total_lines=0,
                    total_code_lines=0,
                    total_nodes=0,
                    average_complexity=0,
                    max_complexity=0,
                    total_imports=0
                ),
                languages=[]
            )
            
        except Exception as e:
            logger.error(f"Project analysis failed for {input.directory_path}: {e}")
            return AnalysisError(input.directory_path, e)
    
    @strawberry.field
    async def search_symbols(
        self, 
        info: strawberry.Info, 
        input: SymbolSearchInput
    ) -> List[UniversalNodeTypeEnhanced]:
        """Search for symbols across the codebase."""
        context: Context = info.context
        
        try:
            # This would implement symbol search using the intelligence engine
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Symbol search failed: {e}")
            return []
    
    @strawberry.field
    async def get_symbol(
        self, 
        info: strawberry.Info, 
        symbol_id: str
    ) -> Union[UniversalNodeTypeEnhanced, ValidationError, InternalError]:
        """Get a specific symbol by ID."""
        context: Context = info.context
        
        try:
            symbol_data = await context.dataloaders.symbol_loader.load(symbol_id)
            if symbol_data:
                return UniversalNodeTypeEnhanced._convert_to_enhanced(symbol_data)
            else:
                return ValidationError(field="symbol_id", message="Symbol not found")
                
        except Exception as e:
            logger.error(f"Symbol lookup failed for {symbol_id}: {e}")
            return InternalError(error_id="symbol_lookup", details=str(e))


@strawberry.type
class Mutation:
    """GraphQL mutations for code analysis operations."""
    
    @strawberry.mutation
    async def refresh_analysis(
        self, 
        info: strawberry.Info, 
        project_id: str
    ) -> bool:
        """Refresh analysis for a project."""
        context: Context = info.context
        
        try:
            # Clear caches
            context.dataloaders.clear_all_caches()
            
            # Trigger re-analysis (implementation depends on your requirements)
            logger.info(f"Refreshed analysis for project: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh analysis for project {project_id}: {e}")
            return False


# Create the schema with extensions
def create_schema():
    """Create the GraphQL schema with all extensions."""
    from .extensions import create_extensions
    
    return strawberry.Schema(
        query=Query,
        mutation=Mutation,
        extensions=create_extensions(
            enable_logging=True,
            enable_performance=True,
            enable_validation=True,
            slow_query_threshold=2.0,
            max_query_depth=15
        )
    )
