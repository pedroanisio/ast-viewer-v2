"""Shared metrics and complexity calculation utilities.

This module provides centralized complexity calculations to eliminate 
duplication across adapters (python.py, tree_sitter.py, intelligence.py).

DRY Fix: Eliminates repeated complexity calculation logic.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ComplexityType(Enum):
    """Types of complexity metrics."""
    CYCLOMATIC = "cyclomatic"
    COGNITIVE = "cognitive"
    HALSTEAD = "halstead"
    MAINTAINABILITY = "maintainability"


@dataclass
class ComplexityMetrics:
    """Container for various complexity metrics."""
    cyclomatic: float = 0.0
    cognitive: float = 0.0
    halstead_difficulty: float = 0.0
    halstead_effort: float = 0.0
    maintainability_index: float = 0.0
    lines_of_code: int = 0
    lines_of_comments: int = 0
    nesting_depth: int = 0


class ComplexityCalculator:
    """Centralized complexity calculation to eliminate duplication across adapters."""
    
    @staticmethod
    def calculate_cyclomatic_complexity(node_data: Dict[str, Any]) -> float:
        """Calculate cyclomatic complexity for a code node.
        
        This was duplicated in python.py and tree_sitter.py adapters.
        """
        complexity = 1  # Base complexity
        
        # Decision points that increase complexity
        decision_keywords = {
            'if', 'elif', 'else', 'while', 'for', 'try', 'except', 
            'finally', 'with', 'and', 'or', 'case', 'switch', 'catch'
        }
        
        # Extract relevant data
        node_type = node_data.get('type', '').lower()
        content = node_data.get('content', '')
        children = node_data.get('children', [])
        
        # Count decision points in content
        if isinstance(content, str):
            for keyword in decision_keywords:
                complexity += content.lower().count(keyword)
        
        # Add complexity from specific node types
        if node_type in ['if_statement', 'while_loop', 'for_loop', 'try_statement']:
            complexity += 1
        
        # Add complexity from children
        for child in children:
            if isinstance(child, dict):
                child_type = child.get('type', '').lower()
                if any(decision in child_type for decision in decision_keywords):
                    complexity += 1
        
        return float(complexity)
    
    @staticmethod
    def calculate_cognitive_complexity(node_data: Dict[str, Any]) -> float:
        """Calculate cognitive complexity (human-perceived complexity).
        
        This was duplicated across multiple analyzers.
        """
        complexity = 0.0
        nesting_level = node_data.get('nesting_level', 0)
        
        # Base cognitive load based on node type
        cognitive_weights = {
            'if_statement': 1,
            'else_statement': 1,
            'elif_statement': 1,
            'while_loop': 2,
            'for_loop': 2,
            'try_statement': 2,
            'except_clause': 2,
            'switch_statement': 2,
            'case_clause': 1,
            'break_statement': 1,
            'continue_statement': 1,
            'return_statement': 1,
            'lambda': 3,
            'nested_function': 3
        }
        
        node_type = node_data.get('type', '').lower()
        base_weight = cognitive_weights.get(node_type, 0)
        
        # Apply nesting penalty
        nesting_penalty = max(0, nesting_level - 1)
        complexity = base_weight + nesting_penalty
        
        return float(complexity)
    
    @staticmethod
    def calculate_nesting_depth(node_data: Dict[str, Any]) -> int:
        """Calculate maximum nesting depth.
        
        This calculation was repeated in multiple places.
        """
        def get_depth(node, current_depth=0):
            max_depth = current_depth
            children = node.get('children', [])
            
            for child in children:
                if isinstance(child, dict):
                    child_depth = get_depth(child, current_depth + 1)
                    max_depth = max(max_depth, child_depth)
            
            return max_depth
        
        return get_depth(node_data)
    
    @staticmethod
    def calculate_halstead_metrics(operators: List[str], operands: List[str]) -> Dict[str, float]:
        """Calculate Halstead complexity metrics.
        
        This was duplicated in multiple analysis modules.
        """
        if not operators and not operands:
            return {
                'difficulty': 0.0,
                'effort': 0.0,
                'volume': 0.0,
                'length': 0.0
            }
        
        # Unique operators and operands
        unique_operators = len(set(operators))
        unique_operands = len(set(operands))
        
        # Total operators and operands
        total_operators = len(operators)
        total_operands = len(operands)
        
        # Halstead metrics
        vocabulary = unique_operators + unique_operands
        length = total_operators + total_operands
        
        if vocabulary > 0 and unique_operands > 0:
            volume = length * (vocabulary.bit_length() if vocabulary > 0 else 0)
            difficulty = (unique_operators / 2.0) * (total_operands / unique_operands)
            effort = difficulty * volume
        else:
            volume = difficulty = effort = 0.0
        
        return {
            'difficulty': difficulty,
            'effort': effort,
            'volume': volume,
            'length': float(length)
        }
    
    @staticmethod
    def calculate_maintainability_index(
        cyclomatic_complexity: float,
        halstead_volume: float,
        lines_of_code: int,
        comment_ratio: float = 0.0
    ) -> float:
        """Calculate maintainability index.
        
        This formula was repeated across multiple analysis modules.
        """
        import math
        
        if lines_of_code == 0:
            return 100.0
        
        # Standard maintainability index formula
        mi = (171 - 5.2 * math.log(halstead_volume) 
              - 0.23 * cyclomatic_complexity 
              - 16.2 * math.log(lines_of_code))
        
        # Add comment bonus
        if comment_ratio > 0:
            mi += 50.0 * math.sin(math.sqrt(2.4 * comment_ratio))
        
        # Normalize to 0-100 scale
        return max(0.0, min(100.0, mi))
    
    @classmethod
    def calculate_comprehensive_metrics(
        cls, 
        node_data: Dict[str, Any],
        operators: Optional[List[str]] = None,
        operands: Optional[List[str]] = None
    ) -> ComplexityMetrics:
        """Calculate all complexity metrics for a node.
        
        This comprehensive calculation eliminates the need for separate
        calculations in each adapter.
        """
        operators = operators or []
        operands = operands or []
        
        # Calculate all metrics
        cyclomatic = cls.calculate_cyclomatic_complexity(node_data)
        cognitive = cls.calculate_cognitive_complexity(node_data)
        nesting_depth = cls.calculate_nesting_depth(node_data)
        
        halstead = cls.calculate_halstead_metrics(operators, operands)
        
        lines_of_code = node_data.get('lines_of_code', 0)
        lines_of_comments = node_data.get('lines_of_comments', 0)
        comment_ratio = lines_of_comments / max(1, lines_of_code)
        
        maintainability = cls.calculate_maintainability_index(
            cyclomatic, halstead['volume'], lines_of_code, comment_ratio
        )
        
        return ComplexityMetrics(
            cyclomatic=cyclomatic,
            cognitive=cognitive,
            halstead_difficulty=halstead['difficulty'],
            halstead_effort=halstead['effort'],
            maintainability_index=maintainability,
            lines_of_code=lines_of_code,
            lines_of_comments=lines_of_comments,
            nesting_depth=nesting_depth
        )


class MetricsCollector:
    """Collect and aggregate metrics across multiple code elements."""
    
    def __init__(self):
        self.metrics: List[ComplexityMetrics] = []
        self.aggregated: Optional[Dict[str, Any]] = None
    
    def add_metrics(self, metrics: ComplexityMetrics):
        """Add metrics for a code element."""
        self.metrics.append(metrics)
        self.aggregated = None  # Reset aggregation
    
    def add_node_metrics(
        self, 
        node_data: Dict[str, Any],
        operators: Optional[List[str]] = None,
        operands: Optional[List[str]] = None
    ):
        """Calculate and add metrics for a node."""
        metrics = ComplexityCalculator.calculate_comprehensive_metrics(
            node_data, operators, operands
        )
        self.add_metrics(metrics)
    
    def get_aggregated_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics across all collected metrics."""
        if self.aggregated is not None:
            return self.aggregated
        
        if not self.metrics:
            return {
                'count': 0,
                'avg_cyclomatic': 0.0,
                'max_cyclomatic': 0.0,
                'avg_cognitive': 0.0,
                'max_cognitive': 0.0,
                'avg_maintainability': 0.0,
                'total_lines': 0,
                'max_nesting': 0
            }
        
        # Calculate aggregations
        cyclomatic_values = [m.cyclomatic for m in self.metrics]
        cognitive_values = [m.cognitive for m in self.metrics]
        maintainability_values = [m.maintainability_index for m in self.metrics]
        
        self.aggregated = {
            'count': len(self.metrics),
            'avg_cyclomatic': sum(cyclomatic_values) / len(cyclomatic_values),
            'max_cyclomatic': max(cyclomatic_values),
            'avg_cognitive': sum(cognitive_values) / len(cognitive_values),
            'max_cognitive': max(cognitive_values),
            'avg_maintainability': sum(maintainability_values) / len(maintainability_values),
            'total_lines': sum(m.lines_of_code for m in self.metrics),
            'max_nesting': max(m.nesting_depth for m in self.metrics)
        }
        
        return self.aggregated
    
    def get_complexity_distribution(self) -> Dict[str, int]:
        """Get distribution of complexity levels."""
        distribution = {'low': 0, 'medium': 0, 'high': 0, 'very_high': 0}
        
        for metrics in self.metrics:
            complexity = metrics.cyclomatic
            if complexity <= 5:
                distribution['low'] += 1
            elif complexity <= 10:
                distribution['medium'] += 1
            elif complexity <= 20:
                distribution['high'] += 1
            else:
                distribution['very_high'] += 1
        
        return distribution
    
    def get_quality_score(self) -> float:
        """Calculate overall code quality score (0-100)."""
        if not self.metrics:
            return 0.0
        
        aggregated = self.get_aggregated_metrics()
        
        # Weighted quality score
        complexity_score = max(0, 100 - aggregated['avg_cyclomatic'] * 5)
        maintainability_score = aggregated['avg_maintainability']
        
        # Combine scores
        quality_score = (complexity_score * 0.4 + maintainability_score * 0.6)
        return min(100.0, max(0.0, quality_score))
