"""Memory Store - ChromaDB integration for vector storage"""

import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime

from config import config


class MemoryStore:
    """ChromaDB-backed memory storage for learning"""
    
    def __init__(self):
        self._client = None
        self._collections = {}
        self.config = config
    
    def _get_client(self):
        """Lazy-load ChromaDB client"""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
                
                self._client = chromadb.HttpClient(
                    host=self.config.chroma_host,
                    port=self.config.chroma_port,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
            except ImportError:
                # Fallback to in-memory storage
                self._client = "memory"
            except Exception:
                self._client = "memory"
        
        return self._client
    
    def _get_collection(self, name: str):
        """Get or create a collection"""
        if name not in self._collections:
            client = self._get_client()
            
            if client == "memory":
                self._collections[name] = InMemoryCollection(name)
            else:
                try:
                    self._collections[name] = client.get_or_create_collection(
                        name=f"{self.config.chroma_collection_name}_{name}",
                        metadata={"description": f"Storage for {name}"}
                    )
                except:
                    self._collections[name] = InMemoryCollection(name)
        
        return self._collections[name]
    
    def add_bug_pattern(self, bug_type: str, language: str, framework: str, 
                        fix: str, context: Optional[Dict] = None) -> str:
        """Store a bug pattern for future reference"""
        collection = self._get_collection("bug_patterns")
        
        doc_id = hashlib.md5(f"{bug_type}:{language}:{framework}:{fix}".encode()).hexdigest()
        
        document = json.dumps({
            "bug_type": bug_type,
            "language": language,
            "framework": framework,
            "fix": fix,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        })
        
        collection.upsert(
            ids=[doc_id],
            documents=[document],
            metadatas=[{"bug_type": bug_type, "language": language}]
        )
        
        return doc_id
    
    def search_bug_patterns(self, query: str, language: Optional[str] = None, 
                           limit: int = 5) -> List[Dict]:
        """Search for similar bug patterns"""
        collection = self._get_collection("bug_patterns")
        
        results = collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        patterns = []
        if results and results.get("documents"):
            for doc in results["documents"][0]:
                try:
                    pattern = json.loads(doc)
                    if language is None or pattern.get("language") == language:
                        patterns.append(pattern)
                except:
                    pass
        
        return patterns
    
    def add_architecture_pattern(self, architecture: str, performance: Dict,
                                 language: str, framework: str) -> str:
        """Store architecture performance data"""
        collection = self._get_collection("architecture")
        
        doc_id = hashlib.md5(f"{architecture}:{language}:{framework}".encode()).hexdigest()
        
        document = json.dumps({
            "architecture": architecture,
            "performance": performance,
            "language": language,
            "framework": framework,
            "timestamp": datetime.now().isoformat()
        })
        
        collection.upsert(
            ids=[doc_id],
            documents=[document],
            metadatas=[{"architecture": architecture, "language": language}]
        )
        
        return doc_id
    
    def search_architectures(self, requirements: str, limit: int = 3) -> List[Dict]:
        """Search for similar architecture patterns"""
        collection = self._get_collection("architecture")
        
        results = collection.query(
            query_texts=[requirements],
            n_results=limit
        )
        
        architectures = []
        if results and results.get("documents"):
            for doc in results["documents"][0]:
                try:
                    architectures.append(json.loads(doc))
                except:
                    pass
        
        return architectures
    
    def add_algorithm(self, name: str, code: str, complexity: str,
                      use_cases: List[str], performance: Dict) -> str:
        """Store algorithm implementation"""
        collection = self._get_collection("algorithms")
        
        doc_id = hashlib.md5(f"{name}:{complexity}".encode()).hexdigest()
        
        document = json.dumps({
            "name": name,
            "code": code,
            "complexity": complexity,
            "use_cases": use_cases,
            "performance": performance,
            "timestamp": datetime.now().isoformat()
        })
        
        collection.upsert(
            ids=[doc_id],
            documents=[document],
            metadatas=[{"name": name, "complexity": complexity}]
        )
        
        return doc_id
    
    def search_algorithms(self, problem: str, language: Optional[str] = None,
                         limit: int = 5) -> List[Dict]:
        """Search for relevant algorithms"""
        collection = self._get_collection("algorithms")
        
        results = collection.query(
            query_texts=[problem],
            n_results=limit
        )
        
        algorithms = []
        if results and results.get("documents"):
            for doc in results["documents"][0]:
                try:
                    algo = json.loads(doc)
                    algorithms.append(algo)
                except:
                    pass
        
        return algorithms
    
    def add_project_learning(self, project_id: str, requirements: str,
                            results: Dict, lessons: List[str]) -> str:
        """Store learning from a completed project"""
        collection = self._get_collection("projects")
        
        document = json.dumps({
            "project_id": project_id,
            "requirements": requirements,
            "results": results,
            "lessons": lessons,
            "timestamp": datetime.now().isoformat()
        })
        
        collection.upsert(
            ids=[project_id],
            documents=[document],
            metadatas=[{"requirements": requirements[:100]}]
        )
        
        return project_id
    
    def get_similar_projects(self, requirements: str, limit: int = 3) -> List[Dict]:
        """Find similar past projects"""
        collection = self._get_collection("projects")
        
        results = collection.query(
            query_texts=[requirements],
            n_results=limit
        )
        
        projects = []
        if results and results.get("documents"):
            for doc in results["documents"][0]:
                try:
                    projects.append(json.loads(doc))
                except:
                    pass
        
        return projects
    
    def get_stats(self) -> Dict[str, int]:
        """Get memory statistics"""
        stats = {}
        for name in ["bug_patterns", "architecture", "algorithms", "projects"]:
            collection = self._get_collection(name)
            stats[name] = collection.count()
        return stats


class InMemoryCollection:
    """Fallback in-memory collection when ChromaDB is unavailable"""
    
    def __init__(self, name: str):
        self.name = name
        self._documents = {}
        self._metadatas = {}
    
    def upsert(self, ids: List[str], documents: List[str], 
               metadatas: List[Dict]) -> None:
        for i, id_ in enumerate(ids):
            self._documents[id_] = documents[i]
            self._metadatas[id_] = metadatas[i]
    
    def query(self, query_texts: List[str], n_results: int) -> Dict:
        # Simple keyword matching
        query = query_texts[0].lower()
        
        scored = []
        for doc_id, doc in self._documents.items():
            score = 0
            doc_lower = doc.lower()
            for word in query.split():
                if word in doc_lower:
                    score += 1
            if score > 0:
                scored.append((score, doc_id, doc))
        
        scored.sort(reverse=True)
        top_docs = [doc for _, _, doc in scored[:n_results]]
        
        return {"documents": [top_docs]} if top_docs else {"documents": [[]]}
    
    def count(self) -> int:
        return len(self._documents)


# Global memory store instance
memory_store = MemoryStore()


def get_memory_stats() -> Dict[str, Any]:
    """Get memory statistics"""
    return {
        "stats": memory_store.get_stats(),
        "timestamp": datetime.now().isoformat()
    }


def add_to_memory(memory: Dict, plan: Dict, test_results: Dict, 
                  build_result: Dict, runtime_metrics: Dict) -> Dict:
    """
    Update learning memory with project results.
    
    This is the main entry point called from the main pipeline.
    """
    
    # Store bug patterns if tests failed
    if not test_results.get("passed", True):
        logs = test_results.get("logs", "")
        if "error" in logs.lower() or "failed" in logs.lower():
            memory_store.add_bug_pattern(
                bug_type="test_failure",
                language=plan.get("language", "unknown"),
                framework=plan.get("framework", "unknown"),
                fix="See debug logs for details",
                context={"logs": logs[:1000]}
            )
    
    # Store architecture performance
    memory_store.add_architecture_pattern(
        architecture=plan.get("architecture", "unknown"),
        performance=runtime_metrics,
        language=plan.get("language", "unknown"),
        framework=plan.get("framework", "unknown")
    )
    
    # Update in-memory dict for quick access
    memory["bug_patterns"].append({
        "type": "test_failure" if not test_results.get("passed") else "none",
        "timestamp": datetime.now().isoformat()
    })
    
    memory["architecture_graph"].append({
        "pattern": plan.get("architecture"),
        "performance": runtime_metrics,
        "timestamp": datetime.now().isoformat()
    })
    
    memory["algorithm_library"].append({
        "framework": plan.get("framework"),
        "language": plan.get("language"),
        "timestamp": datetime.now().isoformat()
    })
    
    memory["meta_learning_index"].append({
        "project_complete": True,
        "test_passed": test_results.get("passed"),
        "build_success": build_result.get("success"),
        "timestamp": datetime.now().isoformat()
    })
    
    # Add ChromaDB stats
    memory["chroma_stats"] = memory_store.get_stats()
    
    return memory
