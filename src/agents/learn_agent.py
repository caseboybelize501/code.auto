"""Learn Agent - Update learning memory from project outcomes"""

from typing import Dict, Any, List
from datetime import datetime

from src.memory.memory_store import memory_store, add_to_memory


def update_learning_memory(memory: Dict[str, Any], plan: Dict[str, Any],
                           test_results: Dict[str, Any], build_result: Dict[str, Any],
                           runtime_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update all memory layers with learning from this project.
    
    Args:
        memory: Current memory state
        plan: Project plan that was executed
        test_results: Results from test execution
        build_result: Results from build process
        runtime_metrics: Runtime performance metrics
        
    Returns:
        Updated memory state
    """
    
    # Use the centralized memory store function
    updated_memory = add_to_memory(
        memory=memory,
        plan=plan,
        test_results=test_results,
        build_result=build_result,
        runtime_metrics=runtime_metrics
    )
    
    # Additional learning layers
    
    # 1. Bug Pattern Memory - extract specific bugs
    if not test_results.get("passed", True):
        _learn_from_failures(memory, test_results, plan)
    
    # 2. Architecture Performance - record what worked
    _learn_architecture_performance(memory, plan, runtime_metrics)
    
    # 3. Build Success Patterns
    _learn_build_patterns(memory, plan, build_result)
    
    # 4. Deployment Learnings
    _learn_deployment_patterns(memory, plan, runtime_metrics)
    
    return updated_memory


def _learn_from_failures(memory: Dict, test_results: Dict, plan: Dict) -> None:
    """Extract and store bug patterns from test failures"""
    
    logs = test_results.get("logs", "")
    errors = test_results.get("errors", [])
    
    # Parse error types
    error_types = []
    if "SyntaxError" in logs:
        error_types.append("syntax")
    if "ImportError" in logs or "ModuleNotFoundError" in logs:
        error_types.append("import")
    if "AssertionError" in logs:
        error_types.append("assertion")
    if "TypeError" in logs:
        error_types.append("type")
    if "KeyError" in logs:
        error_types.append("key")
    if "IndexError" in logs:
        error_types.append("index")
    if "AttributeError" in logs:
        error_types.append("attribute")
    if "TimeoutError" in logs:
        error_types.append("timeout")
    
    for error_type in error_types:
        memory_store.add_bug_pattern(
            bug_type=f"test_{error_type}",
            language=plan.get("language", "unknown"),
            framework=plan.get("framework", "unknown"),
            fix=f"Review {error_type} errors in test logs",
            context={"errors": errors[:5] if errors else []}
        )


def _learn_architecture_performance(memory: Dict, plan: Dict, 
                                    runtime_metrics: Dict) -> None:
    """Store architecture performance data"""
    
    architecture = plan.get("architecture", "unknown")
    framework = plan.get("framework", "unknown")
    language = plan.get("language", "unknown")
    
    # Extract key performance indicators
    performance = {
        "latency": runtime_metrics.get("latency", "unknown"),
        "throughput": runtime_metrics.get("throughput", "unknown"),
        "cpu_usage": runtime_metrics.get("cpu_usage", "unknown"),
        "memory_usage": runtime_metrics.get("memory_usage", "unknown"),
        "error_rate": runtime_metrics.get("error_rate", "unknown")
    }
    
    memory_store.add_architecture_pattern(
        architecture=architecture,
        performance=performance,
        language=language,
        framework=framework
    )


def _learn_build_patterns(memory: Dict, plan: Dict, build_result: Dict) -> None:
    """Learn from build success/failure patterns"""
    
    success = build_result.get("success", False)
    errors = build_result.get("compile_errors", [])
    warnings = build_result.get("warnings", [])
    
    if success:
        # Store successful build pattern
        memory_store.add_algorithm(
            name=f"build_{plan.get('language', 'unknown')}",
            code="",
            complexity="O(1)",
            use_cases=["successful build"],
            performance={"build_time": build_result.get("build_time", 0)}
        )
    else:
        # Store build failure pattern
        for error in errors:
            memory_store.add_bug_pattern(
                bug_type="build_error",
                language=plan.get("language", "unknown"),
                framework=plan.get("framework", "unknown"),
                fix="Review build configuration and dependencies",
                context={"error": error}
            )


def _learn_deployment_patterns(memory: Dict, plan: Dict, 
                               runtime_metrics: Dict) -> None:
    """Learn from deployment outcomes"""
    
    # Store deployment success metrics
    memory_store.add_algorithm(
        name=f"deploy_{plan.get('architecture', 'unknown')}",
        code="",
        complexity="O(1)",
        use_cases=["deployment"],
        performance={
            "startup_time": "measured",
            "health_status": runtime_metrics.get("uptime", "unknown"),
            "stability": runtime_metrics.get("error_rate", "unknown")
        }
    )


def get_learning_recommendations(requirements: str, 
                                 language: str = "python") -> Dict[str, Any]:
    """
    Get recommendations based on past learning.
    
    Args:
        requirements: Project requirements
        language: Target programming language
        
    Returns:
        Recommendations for architecture, algorithms, and potential pitfalls
    """
    
    recommendations = {
        "architecture": [],
        "algorithms": [],
        "pitfalls": [],
        "optimizations": []
    }
    
    # Search for similar past projects
    similar_projects = memory_store.get_similar_projects(requirements, limit=3)
    
    for project in similar_projects:
        if project.get("lessons"):
            recommendations["pitfalls"].extend(project["lessons"])
    
    # Search for relevant algorithms
    algorithms = memory_store.search_algorithms(requirements, language=language, limit=5)
    recommendations["algorithms"] = algorithms
    
    # Search for bug patterns to avoid
    bug_patterns = memory_store.search_bug_patterns(
        requirements, language=language, limit=5
    )
    recommendations["pitfalls"].extend([
        f"Avoid {p['bug_type']}: {p['fix']}" for p in bug_patterns
    ])
    
    # Search for architecture patterns
    architectures = memory_store.search_architectures(requirements, limit=3)
    recommendations["architecture"] = architectures
    
    return recommendations


def get_memory_stats() -> Dict[str, Any]:
    """Get statistics about stored memories"""
    return {
        "stats": memory_store.get_stats(),
        "timestamp": datetime.now().isoformat()
    }
