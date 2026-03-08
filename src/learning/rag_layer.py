"""
RAG Self-Learning Layer - Learns from past projects to improve future generations

This module implements:
- Vector storage of code patterns using ChromaDB
- Semantic search for similar projects
- Learning from successful/failed patterns
- Context augmentation for code generation
"""

import os
import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    chromadb = None

from config import config


class RAGLearningLayer:
    """
    Retrieval-Augmented Generation layer for continuous learning
    
    Stores and retrieves:
    - Code patterns and architectures
    - Successful implementations
    - Bug fixes and solutions
    - Domain-specific patterns
    """
    
    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or os.path.join(config.work_dir, ".rag_store")
        os.makedirs(self.persist_dir, exist_ok=True)
        
        self.collections = {}
        self.initialized = False
        
        if CHROMA_AVAILABLE:
            self._initialize_chroma()
        else:
            self._initialize_fallback()
    
    def _initialize_chroma(self):
        """Initialize ChromaDB for vector storage"""
        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Create collections for different knowledge types
            self.collections = {
                "code_patterns": self._get_or_create_collection("code_patterns"),
                "architectures": self._get_or_create_collection("architectures"),
                "bug_fixes": self._get_or_create_collection("bug_fixes"),
                "domain_patterns": self._get_or_create_collection("domain_patterns"),
                "successful_projects": self._get_or_create_collection("successful_projects")
            }
            
            self.initialized = True
            print(f"RAG Layer initialized with ChromaDB at {self.persist_dir}")
            
        except Exception as e:
            print(f"ChromaDB initialization failed: {e}, using fallback")
            self._initialize_fallback()
    
    def _initialize_fallback(self):
        """Initialize file-based fallback storage"""
        self.storage_file = os.path.join(self.persist_dir, "knowledge_base.json")
        self.knowledge_base = self._load_knowledge_base()
        self.initialized = True
        print(f"RAG Layer initialized with file-based storage at {self.persist_dir}")
    
    def _load_knowledge_base(self) -> Dict:
        """Load or create file-based knowledge base"""
        if os.path.exists(self.storage_file):
            with open(self.storage_file, "r") as f:
                return json.load(f)
        return {
            "code_patterns": [],
            "architectures": [],
            "bug_fixes": [],
            "domain_patterns": [],
            "successful_projects": [],
            "metadata": {
                "total_entries": 0,
                "last_updated": None
            }
        }
    
    def _save_knowledge_base(self):
        """Persist knowledge base to disk"""
        self.knowledge_base["metadata"]["last_updated"] = datetime.now().isoformat()
        self.knowledge_base["metadata"]["total_entries"] = sum(
            len(v) for k, v in self.knowledge_base.items() 
            if k != "metadata"
        )
        with open(self.storage_file, "w") as f:
            json.dump(self.knowledge_base, f, indent=2)
    
    def _get_or_create_collection(self, name: str):
        """Get or create ChromaDB collection"""
        try:
            return self.client.get_or_create_collection(name=name)
        except:
            return None
    
    def learn_from_project(self, project_id: str, plan: Dict, files: List[Dict], 
                          results: Dict, validation: Dict = None):
        """
        Learn from a completed project
        
        Args:
            project_id: Project identifier
            plan: Project plan used
            files: Generated files
            results: Build/test/deployment results
            validation: Validation results
        """
        if not self.initialized:
            return
        
        # Extract learnings
        learnings = self._extract_learnings(project_id, plan, files, results, validation)
        
        # Store in appropriate collections
        if CHROMA_AVAILABLE and self.collections:
            self._store_in_chroma(learnings)
        else:
            self._store_in_fallback(learnings)
    
    def _extract_learnings(self, project_id: str, plan: Dict, files: List[Dict], 
                          results: Dict, validation: Dict) -> Dict:
        """Extract learnings from project"""
        learnings = {
            "project_id": project_id,
            "timestamp": datetime.now().isoformat(),
            "requirements": plan.get("requirements", "")[:500],
            "architecture": plan.get("architecture", ""),
            "language": plan.get("language", ""),
            "framework": plan.get("framework", ""),
            "domain": self._detect_domain(plan),
            "success": results.get("build_result", {}).get("success", False) and 
                      results.get("test_results", {}).get("passed", False),
            "patterns": [],
            "code_samples": [],
            "lessons": []
        }
        
        # Extract patterns from files
        for file_info in files:
            content = file_info.get("content", "")
            filepath = file_info.get("path", "")
            
            # Extract architectural patterns
            patterns = self._detect_patterns(content)
            for pattern in patterns:
                learnings["patterns"].append({
                    "pattern": pattern,
                    "file": filepath,
                    "domain": learnings["domain"]
                })
            
            # Store code samples for successful projects
            if learnings["success"] and len(content) > 50 and len(content) < 5000:
                learnings["code_samples"].append({
                    "path": filepath,
                    "content": content[:2000],  # Truncate for storage
                    "language": filepath.split(".")[-1] if "." in filepath else "text"
                })
        
        # Extract lessons from validation
        if validation:
            if not validation.get("passed", True):
                for issue in validation.get("issues", []):
                    learnings["lessons"].append({
                        "type": "issue",
                        "description": issue,
                        "context": f"Project {project_id} failed validation"
                    })
        
        # Extract lessons from build results
        build_result = results.get("build_result", {})
        if not build_result.get("success", True):
            for error in build_result.get("compile_errors", [])[:3]:
                learnings["lessons"].append({
                    "type": "build_error",
                    "description": error[:500],
                    "context": f"Build failed in {project_id}"
                })
        
        return learnings
    
    def _detect_domain(self, plan: Dict) -> str:
        """Detect project domain from plan"""
        requirements = plan.get("requirements", "").lower()
        
        domain_keywords = {
            "iot": ["iot", "sensor", "telemetry", "device", "mqtt"],
            "finance": ["crypto", "finance", "trading", "portfolio", "payment"],
            "healthcare": ["health", "medical", "patient", "doctor", "appointment"],
            "ecommerce": ["shop", "product", "cart", "order", "inventory"],
            "education": ["course", "student", "learning", "education", "lms"],
            "streaming": ["stream", "kafka", "real-time", "event", "processing"],
            "saas": ["saas", "tenant", "subscription", "billing"],
            "ml": ["ml", "model", "inference", "training", "prediction"],
            "blockchain": ["blockchain", "crypto", "smart contract", "defi"],
            "video": ["video", "transcode", "streaming", "media"],
            "identity": ["auth", "oauth", "sso", "identity", "saml"],
            "geospatial": ["geo", "spatial", "map", "location", "gis"],
        }
        
        for domain, keywords in domain_keywords.items():
            if any(kw in requirements for kw in keywords):
                return domain
        
        return "general"
    
    def _detect_patterns(self, code: str) -> List[str]:
        """Detect design patterns in code"""
        patterns = []
        code_lower = code.lower()
        
        pattern_indicators = {
            "repository": ["repository", "data access", "find_by", "save"],
            "factory": ["factory", "create_", "maker"],
            "singleton": ["singleton", "_instance", "get_instance"],
            "observer": ["observer", "subscribe", "publish", "notify"],
            "decorator": ["decorator", "wrapper", "@"] ,
            "strategy": ["strategy", "algorithm", "implementation"],
            "middleware": ["middleware", "interceptor", "filter"],
            "dependency_injection": ["inject", "container", "provider"],
            "circuit_breaker": ["circuit", "breaker", "retry"],
            "cqrs": ["command", "query", "handler"],
            "api_gateway": ["gateway", "router", "proxy"],
            "event_sourcing": ["event", "source", "append"],
        }
        
        for pattern, indicators in pattern_indicators.items():
            if any(ind in code_lower for ind in indicators):
                patterns.append(pattern)
        
        return patterns
    
    def _store_in_chroma(self, learnings: Dict):
        """Store learnings in ChromaDB"""
        if not self.collections:
            return
        
        # Store in successful projects if applicable
        if learnings["success"]:
            collection = self.collections.get("successful_projects")
            if collection:
                doc_id = f"proj_{learnings['project_id']}"
                collection.upsert(
                    ids=[doc_id],
                    documents=[learnings["requirements"]],
                    metadatas=[{
                        "project_id": learnings["project_id"],
                        "domain": learnings["domain"],
                        "architecture": learnings["architecture"],
                        "success": True
                    }]
                )
        
        # Store patterns
        for pattern in learnings["patterns"]:
            collection = self.collections.get("domain_patterns")
            if collection:
                pattern_id = f"pattern_{learnings['project_id']}_{pattern['pattern']}"
                collection.upsert(
                    ids=[pattern_id],
                    documents=[f"{pattern['pattern']} pattern for {learnings['domain']}"],
                    metadatas=[pattern]
                )
        
        # Store code samples
        for sample in learnings["code_samples"]:
            collection = self.collections.get("code_patterns")
            if collection:
                sample_id = f"code_{learnings['project_id']}_{hashlib.md5(sample['content'].encode()).hexdigest()[:8]}"
                collection.upsert(
                    ids=[sample_id],
                    documents=[sample["content"]],
                    metadatas=[{
                        "project_id": learnings["project_id"],
                        "path": sample["path"],
                        "language": sample["language"],
                        "domain": learnings["domain"]
                    }]
                )
    
    def _store_in_fallback(self, learnings: Dict):
        """Store learnings in file-based storage"""
        if learnings["success"]:
            self.knowledge_base["successful_projects"].append({
                "project_id": learnings["project_id"],
                "requirements": learnings["requirements"],
                "domain": learnings["domain"],
                "architecture": learnings["architecture"],
                "patterns": learnings["patterns"]
            })
        
        for pattern in learnings["patterns"]:
            self.knowledge_base["domain_patterns"].append(pattern)
        
        for sample in learnings["code_samples"]:
            self.knowledge_base["code_patterns"].append({
                **sample,
                "project_id": learnings["project_id"],
                "domain": learnings["domain"]
            })
        
        self._save_knowledge_base()
    
    def get_context_for_requirements(self, requirements: str, 
                                     limit: int = 5) -> Dict[str, List[Dict]]:
        """
        Retrieve relevant context for new requirements
        
        Args:
            requirements: New project requirements
            limit: Max results per category
            
        Returns:
            Dictionary with similar projects, patterns, and code samples
        """
        if not self.initialized:
            return {"projects": [], "patterns": [], "code_samples": []}
        
        if CHROMA_AVAILABLE and self.collections:
            return self._query_chroma(requirements, limit)
        else:
            return self._query_fallback(requirements, limit)
    
    def _query_chroma(self, requirements: str, limit: int) -> Dict:
        """Query ChromaDB for relevant context"""
        results = {
            "projects": [],
            "patterns": [],
            "code_samples": []
        }
        
        try:
            # Query similar projects
            proj_collection = self.collections.get("successful_projects")
            if proj_collection:
                proj_results = proj_collection.query(
                    query_texts=[requirements],
                    n_results=min(limit, proj_collection.count())
                )
                if proj_results and proj_results.get("metadatas"):
                    results["projects"] = proj_results["metadatas"][0]
            
            # Query domain patterns
            pattern_collection = self.collections.get("domain_patterns")
            if pattern_collection:
                pattern_results = pattern_collection.query(
                    query_texts=[requirements],
                    n_results=min(limit, pattern_collection.count())
                )
                if pattern_results and pattern_results.get("metadatas"):
                    results["patterns"] = pattern_results["metadatas"][0]
            
            # Query code samples
            code_collection = self.collections.get("code_patterns")
            if code_collection:
                code_results = code_collection.query(
                    query_texts=[requirements],
                    n_results=min(limit * 2, code_collection.count())
                )
                if code_results and code_results.get("metadatas"):
                    results["code_samples"] = code_results["metadatas"][0]
        
        except Exception as e:
            print(f"ChromaDB query failed: {e}")
        
        return results
    
    def _query_fallback(self, requirements: str, limit: int) -> Dict:
        """Query file-based storage for relevant context"""
        results = {
            "projects": [],
            "patterns": [],
            "code_samples": []
        }
        
        requirements_lower = requirements.lower()
        
        # Find similar projects
        for project in self.knowledge_base.get("successful_projects", []):
            proj_req = project.get("requirements", "").lower()
            # Simple keyword overlap
            overlap = len(set(requirements_lower.split()) & set(proj_req.split()))
            if overlap > 2:
                results["projects"].append(project)
                if len(results["projects"]) >= limit:
                    break
        
        # Find relevant patterns
        domain = self._detect_domain({"requirements": requirements})
        for pattern in self.knowledge_base.get("domain_patterns", []):
            if pattern.get("domain") == domain:
                results["patterns"].append(pattern)
                if len(results["patterns"]) >= limit:
                    break
        
        # Find code samples
        for sample in self.knowledge_base.get("code_patterns", []):
            if sample.get("domain") == domain:
                results["code_samples"].append(sample)
                if len(results["code_samples"]) >= limit * 2:
                    break
        
        return results
    
    def get_learning_summary(self) -> Dict:
        """Get summary of learned knowledge"""
        if CHROMA_AVAILABLE and self.collections:
            summary = {}
            for name, collection in self.collections.items():
                if collection:
                    summary[name] = collection.count()
            return summary
        else:
            return self.knowledge_base.get("metadata", {})
    
    def augment_prompt(self, requirements: str, base_prompt: str) -> str:
        """
        Augment generation prompt with retrieved context
        
        Args:
            requirements: Project requirements
            base_prompt: Original generation prompt
            
        Returns:
            Enhanced prompt with RAG context
        """
        context = self.get_context_for_requirements(requirements)
        
        if not context["projects"] and not context["patterns"]:
            return base_prompt  # No context to add
        
        augmentation = "\n\n--- LEARNED CONTEXT FROM PAST PROJECTS ---\n"
        
        if context["projects"]:
            augmentation += "\nSimilar successful projects:\n"
            for proj in context["projects"][:3]:
                augmentation += f"- {proj.get('architecture', 'Unknown')} architecture for {proj.get('domain', 'unknown')} domain\n"
        
        if context["patterns"]:
            augmentation += "\nRelevant patterns:\n"
            for pattern in context["patterns"][:5]:
                augmentation += f"- {pattern.get('pattern', 'Unknown')} pattern\n"
        
        if context["code_samples"]:
            augmentation += f"\n{len(context['code_samples'])} code samples available for reference\n"
        
        augmentation += "\nUse these patterns and architectures as reference for generating high-quality code.\n"
        augmentation += "--- END CONTEXT ---\n"
        
        return base_prompt + augmentation


# Global instance
rag_layer = RAGLearningLayer()
