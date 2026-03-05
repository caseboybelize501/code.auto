from fastapi import FastAPI
from src.bootstrap.system_scanner import scan_system
from src.planner.dev_planner import plan_project
from src.agents.code_agent import generate_code
from src.agents.test_agent import run_tests
from src.agents.build_agent import build_project
from src.agents.deploy_agent import deploy_project
from src.agents.runtime_agent import monitor_runtime
from src.agents.debug_agent import debug_failure
from src.agents.learn_agent import update_learning_memory
from src.testing.cycle_manager import validate_project
import asyncio

class Jarvis:
    def __init__(self):
        self.system_profile = scan_system()
        self.memory = {
            "bug_patterns": {},
            "architecture_graph": {},
            "algorithm_library": {},
            "meta_learning_index": {}
        }

    async def start_project(self, requirements: str):
        # Step 1: Plan project
        plan = plan_project(requirements)
        
        # Step 2: Generate code
        generated_files = generate_code(plan)
        
        # Step 3: Run tests
        test_results = run_tests(generated_files)
        
        # Step 4: Build project
        build_result = build_project(generated_files)
        
        # Step 5: Deploy project
        deployment_result = deploy_project(generated_files)
        
        # Step 6: Monitor runtime
        runtime_metrics = monitor_runtime(deployment_result)
        
        # Step 7: Debug if needed
        if not test_results["passed"]:
            debug_failure(test_results["logs"])
        
        # Step 8: Update learning memory
        update_learning_memory(self.memory, plan, test_results, build_result, runtime_metrics)
        
        return {
            "status": "completed",
            "metrics": runtime_metrics,
            "memory": self.memory
        }

app = FastAPI()
jarvis = Jarvis()

@app.get("/api/system/profile")
def get_system_profile():
    return jarvis.system_profile

@app.post("/api/project/start")
async def start_project(requirements: str):
    result = await jarvis.start_project(requirements)
    return result

@app.get("/health")
def health_check():
    return {"status": "healthy"}
