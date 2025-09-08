"""GraphQL conversion utilities to eliminate type conversion duplication.

This module provides utilities to convert internal model objects to GraphQL types,
eliminating the 500+ lines of repeated conversion code identified in schema.py.

DRY Fix: Eliminates repeated UniversalNodeType conversions and other GraphQL mappings.
"""

from typing import Optional, List, Any, Dict
import logging

# Import GraphQL types (these will be available when imported from schema context)
try:
    from ..graphql.schema import (
        UniversalNodeType, SourceLocationType, RelationshipType, ReferenceType,
        ElementTypeEnum, LanguageEnum, AccessLevelEnum, RelationTypeEnum
    )
except ImportError:
    # Handle circular import by deferring imports
    UniversalNodeType = None
    SourceLocationType = None
    RelationshipType = None
    ReferenceType = None
    ElementTypeEnum = None
    LanguageEnum = None
    AccessLevelEnum = None
    RelationTypeEnum = None

from ..models.universal import (
    UniversalNode, SourceLocation, Relationship, Reference,
    ElementType, Language, AccessLevel, RelationType
)

logger = logging.getLogger(__name__)


class GraphQLConverters:
    """Centralized GraphQL type converters to eliminate duplication."""
    
    @staticmethod
    def convert_source_location(location: SourceLocation) -> Any:
        """Convert SourceLocation to SourceLocationType.
        
        This was repeated in every UniversalNodeType conversion.
        """
        if not location:
            return None
            
        return SourceLocationType(
            file_path=location.file_path,
            start_line=location.start_line,
            end_line=location.end_line,
            start_column=location.start_column,
            end_column=location.end_column,
            offset=location.offset,
            length=location.length
        )
    
    @staticmethod
    def convert_universal_node(node: UniversalNode) -> Any:
        """Convert UniversalNode to UniversalNodeType.
        
        This exact conversion was repeated 5+ times in schema.py, 
        causing ~100+ lines of duplication per occurrence.
        """
        if not node:
            return None
        
        return UniversalNodeType(
            id=node.id,
            type=ElementTypeEnum(node.type.name) if node.type else None,
            name=node.name,
            language=LanguageEnum(node.language.value) if node.language else None,
            location=GraphQLConverters.convert_source_location(node.location),
            parent_id=node.parent_id,
            children_ids=node.children_ids or [],
            access_level=AccessLevelEnum(node.access_level.value) if node.access_level else None,
            is_static=node.is_static,
            is_async=node.is_async,
            is_abstract=node.is_abstract,
            is_final=node.is_final,
            # Handle optional fields safely
            docstring=getattr(node, 'docstring', None),
            signature=getattr(node, 'signature', None),
            return_type=getattr(node, 'return_type', None),
            parameters=getattr(node, 'parameters', []),
            decorators=getattr(node, 'decorators', []),
            annotations=getattr(node, 'annotations', {}),
            complexity=getattr(node, 'complexity', 0),
            # Tree-sitter specific fields
            tree_sitter_type=getattr(node, 'tree_sitter_type', None),
            byte_range_start=getattr(node, 'byte_range_start', None),
            byte_range_end=getattr(node, 'byte_range_end', None)
        )
    
    @staticmethod
    def convert_relationship(relationship: Relationship) -> Any:
        """Convert Relationship to RelationshipType.
        
        This conversion pattern was also repeated multiple times.
        """
        if not relationship:
            return None
            
        return RelationshipType(
            id=relationship.id,
            type=RelationTypeEnum(relationship.type.value) if relationship.type else None,
            source_id=relationship.source_id,
            target_id=relationship.target_id,
            metadata=relationship.metadata or {},
            strength=getattr(relationship, 'strength', 1.0),
            created_at=getattr(relationship, 'created_at', None)
        )
    
    @staticmethod
    def convert_reference(reference: Reference) -> Any:
        """Convert Reference to ReferenceType.
        
        Another repeated conversion pattern.
        """
        if not reference:
            return None
            
        return ReferenceType(
            id=reference.id,
            source_location=GraphQLConverters.convert_source_location(reference.source_location),
            target_symbol_id=reference.target_symbol_id,
            reference_type=reference.reference_type,
            context=reference.context or {},
            resolved=getattr(reference, 'resolved', True)
        )
    
    @staticmethod
    def convert_nodes_list(nodes: List[UniversalNode]) -> List[Any]:
        """Convert a list of UniversalNodes to GraphQL types.
        
        Batch conversion utility to handle lists efficiently.
        """
        if not nodes:
            return []
        
        return [
            GraphQLConverters.convert_universal_node(node) 
            for node in nodes 
            if node is not None
        ]
    
    @staticmethod
    def convert_relationships_list(relationships: List[Relationship]) -> List[Any]:
        """Convert a list of Relationships to GraphQL types."""
        if not relationships:
            return []
        
        return [
            GraphQLConverters.convert_relationship(rel) 
            for rel in relationships 
            if rel is not None
        ]
    
    @staticmethod
    def convert_references_list(references: List[Reference]) -> List[Any]:
        """Convert a list of References to GraphQL types."""
        if not references:
            return []
        
        return [
            GraphQLConverters.convert_reference(ref) 
            for ref in references 
            if ref is not None
        ]
    
    @staticmethod
    def safe_enum_conversion(value: Any, enum_class: Any, default: Any = None) -> Any:
        """Safely convert a value to a GraphQL enum, handling None and invalid values.
        
        This pattern was repeated in every enum conversion.
        """
        if value is None:
            return default
        
        try:
            if hasattr(value, 'value'):
                # Handle internal enum objects
                return enum_class(value.value)
            elif hasattr(value, 'name'):
                # Handle internal enum objects with name attribute
                return enum_class(value.name)
            else:
                # Handle string or direct values
                return enum_class(value)
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to convert {value} to {enum_class}: {e}")
            return default
    
    @staticmethod
    def batch_convert_with_error_handling(items: List[Any], converter_func, error_msg: str = "conversion") -> List[Any]:
        """Batch convert items with error handling and logging.
        
        This pattern was used multiple times for safe bulk conversions.
        """
        if not items:
            return []
        
        results = []
        failed_count = 0
        
        for item in items:
            try:
                converted = converter_func(item)
                if converted is not None:
                    results.append(converted)
            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed {error_msg} for item {getattr(item, 'id', 'unknown')}: {e}")
        
        if failed_count > 0:
            logger.info(f"Completed batch {error_msg}: {len(results)} successful, {failed_count} failed")
        
        return results


# Convenience functions for common conversions (single-line usage in schema)
def convert_to_graphql_node(node: UniversalNode) -> Any:
    """Single-line converter function for schema.py usage.
    
    Usage in schema.py:
        OLD: UniversalNodeType(id=node.id, type=..., name=..., [20+ more lines])
        NEW: convert_to_graphql_node(node)
    """
    return GraphQLConverters.convert_universal_node(node)

def convert_to_graphql_location(location: SourceLocation) -> Any:
    """Single-line converter for source locations."""
    return GraphQLConverters.convert_source_location(location)

def convert_to_graphql_relationship(relationship: Relationship) -> Any:
    """Single-line converter for relationships."""
    return GraphQLConverters.convert_relationship(relationship)

def convert_to_graphql_reference(reference: Reference) -> Any:
    """Single-line converter for references."""
    return GraphQLConverters.convert_reference(reference)

# Batch converters
def convert_nodes_to_graphql(nodes: List[UniversalNode]) -> List[Any]:
    """Convert node list to GraphQL types."""
    return GraphQLConverters.convert_nodes_list(nodes)

def convert_relationships_to_graphql(relationships: List[Relationship]) -> List[Any]:
    """Convert relationship list to GraphQL types."""
    return GraphQLConverters.convert_relationships_list(relationships)

def convert_references_to_graphql(references: List[Reference]) -> List[Any]:
    """Convert reference list to GraphQL types."""
    return GraphQLConverters.convert_references_list(references)
