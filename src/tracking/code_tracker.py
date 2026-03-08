"""
Code Tracking Manager - Tracks all generated code for RAG learning

This module handles:
- Code artifact storage and versioning
- Metadata extraction from generated code
- Project-to-code mapping
- Retrieval interface for RAG layer
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from config import config


class CodeTrackingManager:
    """Manages code artifact tracking and retrieval"""
    
    def __init__(self, tracking_dir: str = None):
        self.tracking_dir = tracking_dir or os.path.join(config.work_dir, ".tracking")
        self.index_file = os.path.join(self.tracking_dir, "code_index.json")
        self.metadata_dir = os.path.join(self.tracking_dir, "metadata")
        self.snippets_dir = os.path.join(self.tracking_dir, "snippets")
        
        os.makedirs(self.tracking_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        os.makedirs(self.snippets_dir, exist_ok=True)
        
        self.index = self._load_index()
    
    def _load_index(self) -> Dict:
        """Load or create code index"""
        if os.path.exists(self.index_file):
            with open(self.index_file, "r") as f:
                return json.load(f)
        return {
            "projects": {},
            "total_files": 0,
            "total_lines": 0,
            "last_updated": None
        }
    
    def _save_index(self):
        """Persist index to disk"""
        self.index["last_updated"] = datetime.now().isoformat()
        with open(self.index_file, "w") as f:
            json.dump(self.index, f, indent=2)
    
    def track_project(self, project_id: str, files: List[Dict], plan: Dict, 
                      results: Dict = None) -> Dict[str, Any]:
        """
        Track all code from a generated project
        
        Args:
            project_id: Unique project identifier
            files: List of generated file dicts with name, content, path
            plan: Project plan used for generation
            results: Build/test/deployment results
            
        Returns:
            Tracking summary
        """
        project_record = {
            "project_id": project_id,
            "timestamp": datetime.now().isoformat(),
            "plan": self._extract_plan_summary(plan),
            "files": [],
            "code_snippets": [],
            "patterns": [],
            "metrics": {}
        }
        
        total_lines = 0
        
        for file_info in files:
            file_record = self._track_file(
                project_id, 
                file_info,
                plan.get("language", "python")
            )
            project_record["files"].append(file_record)
            total_lines += file_record.get("line_count", 0)
            
            # Extract code snippets for RAG
            snippets = self._extract_snippets(file_info, project_id)
            project_record["code_snippets"].extend(snippets)
            
            # Extract patterns
            patterns = self._extract_patterns(file_info, plan)
            project_record["patterns"].extend(patterns)
        
        # Add results if available
        if results:
            project_record["results"] = self._extract_results_summary(results)
        
        # Update metrics
        project_record["metrics"] = {
            "total_files": len(files),
            "total_lines": total_lines,
            "total_snippets": len(project_record["code_snippets"]),
            "total_patterns": len(project_record["patterns"])
        }
        
        # Store in index
        self.index["projects"][project_id] = project_record
        self.index["total_files"] += len(files)
        self.index["total_lines"] += total_lines
        
        # Save project metadata
        self._save_project_metadata(project_id, project_record)
        self._save_index()
        
        return {
            "project_id": project_id,
            "files_tracked": len(files),
            "snippets_extracted": len(project_record["code_snippets"]),
            "patterns_found": len(project_record["patterns"]),
            "total_lines": total_lines
        }
    
    def _track_file(self, project_id: str, file_info: Dict, language: str) -> Dict:
        """Track individual file"""
        content = file_info.get("content", "")
        filepath = file_info.get("path", file_info.get("name", "unknown"))
        
        # Calculate hash for deduplication
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        # Count lines
        lines = content.split("\n")
        line_count = len(lines)
        code_lines = sum(1 for l in lines if l.strip() and not l.strip().startswith("#"))
        
        # Extract imports/dependencies
        imports = self._extract_imports(content, language)
        
        # Extract classes and functions
        classes = self._extract_classes(content, language)
        functions = self._extract_functions(content, language)
        
        file_record = {
            "path": filepath,
            "hash": content_hash,
            "line_count": line_count,
            "code_lines": code_lines,
            "imports": imports,
            "classes": classes,
            "functions": functions,
            "language": language
        }
        
        return file_record
    
    def _extract_snippets(self, file_info: Dict, project_id: str) -> List[Dict]:
        """Extract meaningful code snippets for RAG"""
        snippets = []
        content = file_info.get("content", "")
        filepath = file_info.get("path", "unknown")
        language = filepath.split(".")[-1] if "." in filepath else "python"
        
        # Split into logical chunks (classes, functions, blocks)
        if language == "py":
            # Extract class definitions
            import re
            class_pattern = r'(class\s+\w+[^:]+:.*?)(?=\nclass\s|\nif\s|\n__main__|$)'
            classes = re.findall(class_pattern, content, re.DOTALL)
            
            for i, cls in enumerate(classes):
                snippet_id = f"{project_id}_{filepath}_class_{i}"
                snippets.append({
                    "id": snippet_id,
                    "type": "class",
                    "content": cls.strip(),
                    "source": filepath,
                    "project_id": project_id,
                    "language": "python"
                })
            
            # Extract function definitions
            func_pattern = r'(def\s+\w+\s*\([^)]*\)[^:]+:.*?)(?=\ndef\s|\nclass\s|$)'
            functions = re.findall(func_pattern, content, re.DOTALL)
            
            for i, func in enumerate(functions):
                snippet_id = f"{project_id}_{filepath}_func_{i}"
                snippets.append({
                    "id": snippet_id,
                    "type": "function",
                    "content": func.strip(),
                    "source": filepath,
                    "project_id": project_id,
                    "language": "python"
                })
        
        # Save snippets to disk
        for snippet in snippets:
            snippet_file = os.path.join(self.snippets_dir, f"{snippet['id']}.json")
            with open(snippet_file, "w") as f:
                json.dump(snippet, f, indent=2)
        
        return snippets
    
    def _extract_patterns(self, file_info: Dict, plan: Dict) -> List[Dict]:
        """Extract architectural and design patterns from code"""
        patterns = []
        content = file_info.get("content", "")
        filepath = file_info.get("path", "")
        
        # Pattern detection keywords
        pattern_keywords = {
            "repository": ["repository", "repo", "data access"],
            "factory": ["factory", "creator", "create_"],
            "singleton": ["singleton", "_instance", "get_instance"],
            "observer": ["observer", "subscriber", "publish", "emit"],
            "decorator": ["decorator", "@", "wrapper"],
            "strategy": ["strategy", "algorithm", "implementation"],
            "middleware": ["middleware", "interceptor", "filter"],
            "dependency_injection": ["dependency", "inject", "container"],
            "circuit_breaker": ["circuit", "breaker", "retry"],
            "cqrs": ["command", "query", "cqrs"],
            "event_sourcing": ["event", "source", "append"],
        }
        
        content_lower = content.lower()
        for pattern, keywords in pattern_keywords.items():
            if any(kw in content_lower for kw in keywords):
                patterns.append({
                    "pattern": pattern,
                    "confidence": "high" if len([k for k in keywords if k in content_lower]) > 1 else "medium",
                    "source": filepath,
                    "evidence": [k for k in keywords if k in content_lower][:3]
                })
        
        return patterns
    
    def _extract_imports(self, content: str, language: str) -> List[str]:
        """Extract import statements"""
        imports = []
        if language == "python":
            import re
            # Match 'import x' and 'from x import y'
            import_patterns = [
                r'^import\s+([\w.]+)',
                r'^from\s+([\w.]+)\s+import'
            ]
            for pattern in import_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                imports.extend(matches)
        return list(set(imports))
    
    def _extract_classes(self, content: str, language: str) -> List[str]:
        """Extract class names"""
        classes = []
        if language == "python":
            import re
            matches = re.findall(r'class\s+(\w+)', content)
            classes = matches
        return classes
    
    def _extract_functions(self, content: str, language: str) -> List[str]:
        """Extract function names"""
        functions = []
        if language == "python":
            import re
            matches = re.findall(r'def\s+(\w+)', content)
            functions = matches
        return functions
    
    def _extract_plan_summary(self, plan: Dict) -> Dict:
        """Extract key info from plan for indexing"""
        return {
            "requirements": plan.get("requirements", "")[:200],
            "architecture": plan.get("architecture", ""),
            "language": plan.get("language", ""),
            "framework": plan.get("framework", ""),
            "key_features": plan.get("key_features", [])
        }
    
    def _extract_results_summary(self, results: Dict) -> Dict:
        """Extract key results for indexing"""
        return {
            "build_success": results.get("build_result", {}).get("success", False),
            "tests_passed": results.get("test_results", {}).get("passed", False),
            "deployment_success": results.get("deployment", {}).get("success", False)
        }
    
    def _save_project_metadata(self, project_id: str, record: Dict):
        """Save detailed project metadata"""
        metadata_file = os.path.join(self.metadata_dir, f"{project_id}.json")
        with open(metadata_file, "w") as f:
            json.dump(record, f, indent=2)
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get tracked project by ID"""
        return self.index["projects"].get(project_id)
    
    def search_code(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search code snippets by keyword
        
        Args:
            query: Search query
            limit: Max results
            
        Returns:
            List of matching snippets
        """
        results = []
        query_lower = query.lower()
        
        for project_id, project in self.index["projects"].items():
            for snippet in project.get("code_snippets", []):
                if query_lower in snippet.get("content", "").lower():
                    results.append({
                        "snippet": snippet,
                        "project": project_id,
                        "relevance": 1.0  # Simple keyword match
                    })
                    if len(results) >= limit:
                        return results
        
        return results
    
    def get_similar_code(self, code: str, limit: int = 5) -> List[Dict]:
        """
        Find similar code patterns
        
        Args:
            code: Code to find similar patterns for
            limit: Max results
            
        Returns:
            List of similar code snippets
        """
        # Extract key features from input code
        imports = self._extract_imports(code, "python")
        classes = self._extract_classes(code, "python")
        functions = self._extract_functions(code, "python")
        
        results = []
        
        for project_id, project in self.index["projects"].items():
            score = 0
            
            # Check for similar patterns
            for pattern in project.get("patterns", []):
                results.append({
                    "project_id": project_id,
                    "patterns": project.get("patterns", []),
                    "files": [f["path"] for f in project.get("files", [])],
                    "similarity_score": 0.5  # Placeholder
                })
        
        return results[:limit]
    
    def get_stats(self) -> Dict:
        """Get tracking statistics"""
        return {
            "total_projects": len(self.index["projects"]),
            "total_files": self.index["total_files"],
            "total_lines": self.index["total_lines"],
            "last_updated": self.index["last_updated"]
        }


# Global instance
code_tracker = CodeTrackingManager()
