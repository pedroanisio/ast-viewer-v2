"""DataLoaders for efficient GraphQL query batching and caching."""

from typing import Dict, List, Optional, Any
from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)


class SimpleDataLoader:
    """Simple DataLoader implementation for batching requests."""
    
    def __init__(self, batch_fn, cache=True):
        self.batch_fn = batch_fn
        self.cache_enabled = cache
        self._cache: Dict[str, Any] = {}
        self._pending: Dict[str, asyncio.Future] = {}
        self._batch_queue: List[str] = []
        self._batch_scheduled = False
    
    async def load(self, key: str) -> Any:
        """Load a single item by key."""
        if self.cache_enabled and key in self._cache:
            return self._cache[key]
        
        if key in self._pending:
            return await self._pending[key]
        
        # Create future for this key
        future = asyncio.get_event_loop().create_future()
        self._pending[key] = future
        self._batch_queue.append(key)
        
        # Schedule batch execution if not already scheduled
        if not self._batch_scheduled:
            self._batch_scheduled = True
            asyncio.get_event_loop().call_soon(self._execute_batch)
        
        return await future
    
    async def load_many(self, keys: List[str]) -> List[Any]:
        """Load multiple items by keys."""
        return await asyncio.gather(*[self.load(key) for key in keys])
    
    def _execute_batch(self):
        """Execute the batch and resolve all pending futures."""
        if not self._batch_queue:
            self._batch_scheduled = False
            return
        
        keys = self._batch_queue.copy()
        self._batch_queue.clear()
        self._batch_scheduled = False
        
        asyncio.create_task(self._process_batch(keys))
    
    async def _process_batch(self, keys: List[str]):
        """Process a batch of keys."""
        try:
            results = await self.batch_fn(keys)
            
            for key, result in zip(keys, results):
                if self.cache_enabled:
                    self._cache[key] = result
                
                if key in self._pending:
                    self._pending[key].set_result(result)
                    del self._pending[key]
                    
        except Exception as e:
            # Reject all pending futures
            for key in keys:
                if key in self._pending:
                    self._pending[key].set_exception(e)
                    del self._pending[key]
    
    def clear_cache(self):
        """Clear the cache."""
        self._cache.clear()


class IntelligenceDataLoaders:
    """Collection of DataLoaders for code intelligence queries."""
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
        
        # Create DataLoaders with performance monitoring
        self.symbol_loader = SimpleDataLoader(self._batch_load_symbols)
        self.references_loader = SimpleDataLoader(self._batch_load_references)
        self.relationships_loader = SimpleDataLoader(self._batch_load_relationships)
        self.call_graph_loader = SimpleDataLoader(self._batch_load_call_graph)
        self.dependency_loader = SimpleDataLoader(self._batch_load_dependencies)
        
        # Performance metrics
        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "batch_sizes": [],
            "load_times": []
        }
    
    async def _batch_load_symbols(self, symbol_ids: List[str]) -> List[Optional[Dict[str, Any]]]:
        """Batch load symbols by IDs."""
        results = []
        
        # Get all intelligence data
        for project_id, intelligence in self.analyzer.intelligence_engine.intelligence_cache.items():
            symbols_found = []
            for symbol_id in symbol_ids:
                symbol = intelligence.symbols.get(symbol_id)
                if symbol:
                    symbols_found.append(symbol.model_dump())
                else:
                    symbols_found.append(None)
            results.extend(symbols_found)
            break  # For now, just use first project
        
        # If no intelligence data found, return None for all
        if not results:
            results = [None] * len(symbol_ids)
        
        return results
    
    async def _batch_load_references(self, symbol_ids: List[str]) -> List[List[Dict[str, Any]]]:
        """Batch load references for multiple symbols."""
        results = []
        
        for project_id, intelligence in self.analyzer.intelligence_engine.intelligence_cache.items():
            for symbol_id in symbol_ids:
                references = intelligence.get_symbol_references(symbol_id)
                results.append([ref.model_dump() for ref in references])
            break  # For now, just use first project
        
        if not results:
            results = [[] for _ in symbol_ids]
        
        return results
    
    async def _batch_load_relationships(self, symbol_ids: List[str]) -> List[List[Dict[str, Any]]]:
        """Batch load relationships for multiple symbols."""
        results = []
        
        for project_id, intelligence in self.analyzer.intelligence_engine.intelligence_cache.items():
            for symbol_id in symbol_ids:
                relationships = intelligence.get_symbol_relationships(symbol_id)
                results.append([rel.model_dump() for rel in relationships])
            break  # For now, just use first project
        
        if not results:
            results = [[] for _ in symbol_ids]
        
        return results
    
    async def _batch_load_call_graph(self, symbol_ids: List[str]) -> List[List[Dict[str, Any]]]:
        """Batch load call graph data for multiple symbols."""
        results = []
        
        for project_id, intelligence in self.analyzer.intelligence_engine.intelligence_cache.items():
            for symbol_id in symbol_ids:
                call_data = intelligence.call_graph.get(symbol_id)
                if call_data:
                    results.append(call_data.model_dump())
                else:
                    results.append({})
            break  # For now, just use first project
        
        if not results:
            results = [{} for _ in symbol_ids]
        
        return results
    
    async def _batch_load_dependencies(self, symbol_ids: List[str]) -> List[List[Dict[str, Any]]]:
        """Batch load dependency information for multiple symbols."""
        results = []
        
        for project_id, intelligence in self.analyzer.intelligence_engine.intelligence_cache.items():
            for symbol_id in symbol_ids:
                # Get dependencies from the dependency graph
                dependencies = []
                if intelligence.dependency_graph:
                    for edge in intelligence.dependency_graph.edges:
                        if edge[0] == symbol_id or edge[1] == symbol_id:
                            dependencies.append({
                                "source": edge[0],
                                "target": edge[1],
                                "type": edge[2].value if hasattr(edge[2], 'value') else str(edge[2])
                            })
                results.append(dependencies)
            break  # For now, just use first project
        
        if not results:
            results = [[] for _ in symbol_ids]
        
        return results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get DataLoader performance metrics."""
        return {
            **self.metrics,
            "avg_batch_size": sum(self.metrics["batch_sizes"]) / len(self.metrics["batch_sizes"]) if self.metrics["batch_sizes"] else 0,
            "avg_load_time": sum(self.metrics["load_times"]) / len(self.metrics["load_times"]) if self.metrics["load_times"] else 0
        }
    
    def clear_all_caches(self):
        """Clear all DataLoader caches."""
        self.symbol_loader.clear_cache()
        self.references_loader.clear_cache()
        self.relationships_loader.clear_cache()
        self.call_graph_loader.clear_cache()
        self.dependency_loader.clear_cache()
        
        # Reset metrics
        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "batch_sizes": [],
            "load_times": []
        }
        
        logger.info("Cleared all DataLoader caches and reset metrics")
