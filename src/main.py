"""
JARVIS - Automated Software Development System
Main entry point and FastAPI application
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
import os
import uuid
from datetime import datetime

from config import config

# Import all agents and modules
from src.bootstrap.system_scanner import scan_system
from src.planner.dev_planner import plan_project, get_learning_recommendations
from src.agents.code_agent import generate_code
from src.agents.test_agent import run_tests, generate_tests
from src.agents.build_agent import build_project
from src.agents.validation_agent import validate_code_against_plan, validate_syntax
from src.agents.deploy_agent import deploy_project, stop_container
from src.agents.runtime_agent import monitor_runtime, health_check
from src.agents.debug_agent import debug_failure
from src.agents.learn_agent import update_learning_memory, get_memory_stats
from src.tracking.code_tracker import code_tracker
from src.learning.rag_layer import rag_layer
from src.testing.cycle_manager import validate_project


# ============================================================================
# Pydantic Models
# ============================================================================

class ProjectRequest(BaseModel):
    """Request model for starting a project"""
    requirements: str
    language: Optional[str] = None
    framework: Optional[str] = None
    architecture: Optional[str] = None


class ProjectResponse(BaseModel):
    """Response model for project completion"""
    status: str
    project_id: str
    plan: Optional[Dict] = None
    files: Optional[List[Dict]] = None
    test_results: Optional[Dict] = None
    build_result: Optional[Dict] = None
    deployment: Optional[Dict] = None
    metrics: Optional[Dict] = None
    memory: Optional[Dict] = None
    errors: Optional[List[str]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str


class SystemProfile(BaseModel):
    """System profile response"""
    toolchain: Dict
    dependencies: Dict
    models: Dict
    timestamp: str


# ============================================================================
# Jarvis Class
# ============================================================================

class Jarvis:
    """Main orchestrator for automated software development"""
    
    def __init__(self):
        self.system_profile = self._init_system_scan()
        self.memory = {
            "bug_patterns": [],
            "architecture_graph": [],
            "algorithm_library": [],
            "meta_learning_index": [],
            "chroma_stats": {}
        }
        self.active_projects = {}
        self.active_containers = {}
    
    def _init_system_scan(self) -> Dict:
        """Initialize system profile"""
        try:
            return scan_system()
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def start_project(self, request: ProjectRequest) -> ProjectResponse:
        """
        Execute full software development pipeline.

        Steps:
        1. Get RAG context from past projects
        2. Plan project
        3. Generate code with RAG-augmented context
        4. Validate generated code
        5. Generate tests
        6. Run tests
        7. Build project
        8. Deploy project
        9. Monitor runtime
        10. Debug if needed
        11. Learn from results (RAG storage)
        12. Track code artifacts
        """

        project_id = str(uuid.uuid4())[:8]
        errors = []
        validation_result = None

        try:
            # Step 1: Get RAG context from past projects
            rag_context = rag_layer.get_context_for_requirements(request.requirements)
            
            # Step 2: Plan project (with RAG context if available)
            plan = plan_project(request.requirements)
            
            # Add RAG insights to plan
            if rag_context.get("patterns"):
                plan["rag_patterns"] = [p.get("pattern") for p in rag_context["patterns"][:5]]
            if rag_context.get("projects"):
                plan["similar_projects"] = len(rag_context["projects"])

            # Override with user preferences if provided
            if request.language:
                plan["language"] = request.language
            if request.framework:
                plan["framework"] = request.framework
            if request.architecture:
                plan["architecture"] = request.architecture
            
            # Step 3: Generate code (RAG context is used internally by code_agent)
            generated_files = generate_code(plan, rag_context=rag_context)

            # Step 4: Validate generated code against plan
            validation_result = validate_code_against_plan(generated_files, plan)
            if not validation_result.get("passed", True):
                errors.extend(validation_result.get("issues", []))
            
            # Validate syntax
            syntax_result = validate_syntax(generated_files)
            if not syntax_result.get("passed", True):
                errors.extend(syntax_result.get("errors", []))

            # Step 5: Generate tests
            test_files = generate_tests(generated_files, plan)
            
            # Step 6: Run tests
            test_results = run_tests(generated_files + test_files)

            # Step 7: Build project (non-blocking - warnings don't fail the pipeline)
            build_result = build_project(generated_files)
            if not build_result.get("success", True) and build_result.get("compile_errors"):
                # Build has errors but continue to deployment
                errors.extend(build_result.get("compile_errors", []))
            
            # Add build warnings to errors for visibility
            if build_result.get("warnings"):
                errors.extend(build_result.get("warnings", []))

            # Step 8: Deploy project
            deployment = deploy_project(generated_files)
            
            # Track container for cleanup
            if deployment.get("container_id"):
                self.active_containers[project_id] = deployment["container_id"]

            # Step 9: Monitor runtime
            metrics = monitor_runtime(deployment)

            # Step 10: Debug if tests failed
            debug_result = None
            if not test_results.get("passed", True):
                debug_result = debug_failure(
                    test_results.get("logs", ""),
                    {"project_id": project_id}
                )

            # Compile results for learning
            results = {
                "test_results": test_results,
                "build_result": build_result,
                "deployment": deployment,
                "metrics": metrics,
                "debug_result": debug_result
            }

            # Step 11: Learn from results (RAG storage)
            rag_layer.learn_from_project(
                project_id=project_id,
                plan=plan,
                files=generated_files,
                results=results,
                validation=validation_result
            )
            
            # Step 12: Track code artifacts
            tracking_result = code_tracker.track_project(
                project_id=project_id,
                files=generated_files,
                plan=plan,
                results=results
            )

            # Update learning memory (legacy - kept for backward compatibility)
            self.memory = update_learning_memory(
                self.memory,
                plan,
                test_results,
                build_result,
                metrics
            )

            # Store project
            self.active_projects[project_id] = {
                "plan": plan,
                "files": generated_files,
                "test_results": test_results,
                "build_result": build_result,
                "deployment": deployment,
                "metrics": metrics,
                "debug_result": debug_result,
                "validation": validation_result,
                "tracking": tracking_result,
                "created_at": datetime.now().isoformat()
            }

            return ProjectResponse(
                status="completed" if test_results.get("passed") and build_result.get("success") else "completed_with_issues",
                project_id=project_id,
                plan=plan,
                files=[{"name": f["name"], "path": f["path"]} for f in generated_files],
                test_results=test_results,
                build_result=build_result,
                deployment=deployment,
                metrics=metrics,
                memory={"stats": get_memory_stats(), "rag": rag_layer.get_learning_summary()},
                errors=errors if errors else None
            )

        except Exception as e:
            errors.append(str(e))
            
            # Still try to learn from failed project
            if generated_files and plan:
                rag_layer.learn_from_project(
                    project_id=project_id,
                    plan=plan,
                    files=generated_files,
                    results={"error": str(e)},
                    validation=validation_result
                )
            
            return ProjectResponse(
                status="failed",
                project_id=project_id,
                errors=errors
            )
    
    def get_project_status(self, project_id: str) -> Optional[Dict]:
        """Get status of a project"""
        return self.active_projects.get(project_id)
    
    def cleanup_project(self, project_id: str) -> bool:
        """Cleanup project resources"""
        if project_id in self.active_containers:
            stop_container(self.active_containers[project_id])
            del self.active_containers[project_id]
        
        if project_id in self.active_projects:
            del self.active_projects[project_id]
        
        return True
    
    def get_memory_stats(self) -> Dict:
        """Get memory statistics"""
        return get_memory_stats()
    
    def get_recommendations(self, requirements: str) -> Dict:
        """Get learning-based recommendations"""
        return get_learning_recommendations(requirements)


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="JARVIS API",
    description="Automated Software Development System",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Jarvis
jarvis = Jarvis()


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
def health_check_endpoint():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )


@app.get("/api/system/profile")
def get_system_profile():
    """Get system profile (compilers, tools, dependencies)"""
    return jarvis.system_profile


@app.post("/api/project/start", response_model=ProjectResponse)
async def start_project(request: ProjectRequest):
    """
    Start automated software development pipeline.
    
    This endpoint:
    1. Plans the project architecture
    2. Generates code
    3. Creates and runs tests
    4. Builds the project
    5. Deploys to Docker
    6. Monitors runtime performance
    7. Learns from results
    """
    result = await jarvis.start_project(request)
    return result


@app.get("/api/project/{project_id}")
def get_project_status(project_id: str):
    """Get status and results of a project"""
    project = jarvis.get_project_status(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.delete("/api/project/{project_id}")
def cleanup_project(project_id: str):
    """Cleanup project resources (stop containers, delete files)"""
    success = jarvis.cleanup_project(project_id)
    return {"status": "cleaned" if success else "failed"}


@app.get("/api/memory/stats")
def get_memory_statistics():
    """Get learning memory statistics"""
    return jarvis.get_memory_stats()


@app.post("/api/recommendations")
def get_recommendations(request: ProjectRequest):
    """Get AI recommendations based on past projects"""
    return jarvis.get_recommendations(request.requirements)


@app.get("/api/workspace/files")
def list_workspace_files():
    """List generated files in workspace"""
    workspace = config.work_dir
    files = []
    
    if os.path.exists(workspace):
        for root, dirs, filenames in os.walk(workspace):
            for f in filenames:
                rel_path = os.path.relpath(os.path.join(root, f), workspace)
                files.append(rel_path)
    
    return {"files": files, "workspace": workspace}


@app.get("/api/workspace/file/{path:path}")
def get_workspace_file(path: str):
    """Get content of a workspace file"""
    full_path = os.path.join(config.work_dir, path)
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"path": path, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Ensure workspace exists
    os.makedirs(config.work_dir, exist_ok=True)
    os.makedirs(config.logs_dir, exist_ok=True)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
