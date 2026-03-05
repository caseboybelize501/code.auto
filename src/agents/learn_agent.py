import json

def update_learning_memory(memory, plan, test_results, build_result, runtime_metrics):
    # Update four-layer learning memory
    
    # Layer 1: Bug Pattern Memory
    if not test_results["passed"]:
        memory["bug_patterns"].append({
            "bug_type": "memory leak",
            "language": plan["language"],
            "framework": plan["framework"],
            "fix": "added garbage collection"
        })
    
    # Layer 2: Architecture Performance Graph
    memory["architecture_graph"].append({
        "pattern": plan["architecture"],
        "performance": runtime_metrics,
        "scalability": "high"
    })
    
    # Layer 3: Algorithm Efficiency Library
    memory["algorithm_library"].append({
        "algorithm": "fastapi routing",
        "complexity": "O(1)",
        "performance": runtime_metrics["latency"]
    })
    
    # Layer 4: Meta Learning Index
    memory["meta_learning_index"].append({
        "approach": plan["framework"],
        "debug_cycles": 1,
        "deployment_stability": "high",
        "performance_metrics": runtime_metrics
    })
    
    return memory
