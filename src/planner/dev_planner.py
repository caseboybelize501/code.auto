"""Dev Planner - AI-powered project planning"""

import json
from typing import Dict, Any, Optional
from config import config

from src.llm.client import create_llm_client
from src.memory.memory_store import memory_store


def plan_project(requirements: str) -> Dict[str, Any]:
    """
    Create a project plan based on requirements.
    
    Args:
        requirements: Natural language project requirements
        
    Returns:
        Project plan with architecture, language, framework, etc.
    """
    
    # Try to use LLM for planning if available
    if has_llm_configured():
        try:
            plan = plan_with_llm(requirements)
        except Exception as e:
            print(f"LLM planning failed: {e}, using rule-based planning")
            plan = plan_with_rules(requirements)
    else:
        # Use rule-based planning (works without API key)
        plan = plan_with_rules(requirements)
    
    # Check memory for similar projects
    similar_projects = memory_store.get_similar_projects(requirements, limit=3)
    if similar_projects:
        plan["similar_projects"] = len(similar_projects)
        # Could adjust plan based on past successes
    
    return plan


def has_llm_configured() -> bool:
    """Check if LLM is available (local llama.cpp or cloud)"""
    from config import config
    
    # Check local llama.cpp
    if config.local_llm_enabled:
        return True
    
    # Check cloud providers
    return (config.llm_provider == "openai" and config.openai_api_key) or \
           (config.llm_provider == "anthropic" and config.anthropic_api_key)


def plan_with_llm(requirements: str) -> Dict[str, Any]:
    """Use LLM to create project plan (local or cloud)"""
    from config import config
    from src.llm.client import create_llm_client, check_llama_cpp_available
    
    # Determine which client to use
    if config.local_llm_enabled:
        # Check if llama.cpp is available
        if check_llama_cpp_available(config.local_llm_base_url):
            llm = create_llm_client(
                "llama-cpp",
                base_url=config.local_llm_base_url,
                model=config.local_llm_model,
                context_length=config.local_llm_context_length
            )
        else:
            raise RuntimeError("llama.cpp server not available")
    elif config.llm_provider == "openai" and config.openai_api_key:
        llm = create_llm_client("openai", config.openai_api_key, config.openai_model)
    elif config.llm_provider == "anthropic" and config.anthropic_api_key:
        llm = create_llm_client("anthropic", config.anthropic_api_key, config.anthropic_model)
    else:
        raise RuntimeError("No LLM configured")
    
    system_prompt = """You are an expert software architect. Create a detailed project plan based on requirements.
Consider:
- Scalability requirements
- Performance needs
- Team familiarity (assume Python/JS unless specified)
- Deployment environment
- Best practices for the domain

Respond with valid JSON only."""

    prompt = f"""Create a project plan for these requirements:

{requirements}

Respond with a JSON object in this exact format:
{{
    "requirements": "Brief summary of requirements",
    "architecture": "monolithic OR microservices OR serverless OR event-driven",
    "language": "python OR javascript OR typescript OR go OR rust OR java",
    "framework": "appropriate framework for the language",
    "database": "postgresql OR mongodb OR redis OR sqlite OR mysql",
    "testing_strategy": "unit/integration/e2e balance",
    "deployment_strategy": "docker OR kubernetes OR serverless OR vm",
    "performance_target": "low_latency OR high_throughput OR balanced",
    "estimated_complexity": "low OR medium OR high",
    "key_features": ["list", "of", "main", "features"],
    "recommended_patterns": ["design patterns or architectural patterns"],
    "potential_challenges": ["anticipated challenges"]
}}"""

    response = llm.generate_json(prompt, system_prompt)
    
    # Ensure all required fields exist
    required_fields = [
        "requirements", "architecture", "language", "framework",
        "testing_strategy", "deployment_strategy", "performance_target"
    ]
    
    for field in required_fields:
        if field not in response:
            response[field] = get_default_value(field)
    
    return response


def plan_with_rules(requirements: str) -> Dict[str, Any]:
    """Rule-based planning (fallback when LLM unavailable)"""
    
    requirements_lower = requirements.lower()
    
    # Determine architecture
    if "microservice" in requirements_lower or "scalable" in requirements_lower:
        architecture = "microservices"
    elif "serverless" in requirements_lower or "lambda" in requirements_lower:
        architecture = "serverless"
    elif "real-time" in requirements_lower or "websocket" in requirements_lower:
        architecture = "event-driven"
    else:
        architecture = "monolithic"
    
    # Determine language and framework
    if "python" in requirements_lower:
        language = "python"
        if "api" in requirements_lower or "rest" in requirements_lower:
            framework = "fastapi"
        elif "web" in requirements_lower or "html" in requirements_lower:
            framework = "django"
        else:
            framework = "fastapi"
    elif "node" in requirements_lower or "javascript" in requirements_lower:
        language = "javascript"
        framework = "express"
    elif "typescript" in requirements_lower:
        language = "typescript"
        framework = "nestjs"
    elif "go" in requirements_lower or "golang" in requirements_lower:
        language = "go"
        framework = "gin"
    elif "rust" in requirements_lower:
        language = "rust"
        framework = "actix"
    elif "java" in requirements_lower:
        language = "java"
        framework = "spring-boot"
    else:
        language = "python"
        framework = "fastapi"
    
    # Determine database
    if "sql" in requirements_lower or "relational" in requirements_lower:
        database = "postgresql"
    elif "nosql" in requirements_lower or "document" in requirements_lower:
        database = "mongodb"
    elif "cache" in requirements_lower or "session" in requirements_lower:
        database = "redis"
    elif "simple" in requirements_lower or "small" in requirements_lower:
        database = "sqlite"
    else:
        database = "postgresql"
    
    # Determine deployment
    if "kubernetes" in requirements_lower or "k8s" in requirements_lower:
        deployment = "kubernetes"
    elif "docker" in requirements_lower:
        deployment = "docker"
    elif "aws" in requirements_lower or "azure" in requirements_lower or "gcp" in requirements_lower:
        deployment = "serverless"
    else:
        deployment = "docker"
    
    # Determine performance target
    if "fast" in requirements_lower or "low latency" in requirements_lower or "real-time" in requirements_lower:
        performance = "low_latency"
    elif "high throughput" in requirements_lower or "many users" in requirements_lower:
        performance = "high_throughput"
    else:
        performance = "balanced"

    return {
        "requirements": requirements[:200],
        "architecture": architecture,
        "language": language,
        "framework": framework,
        "database": database,
        "testing_strategy": "unit/integration/e2e",
        "deployment_strategy": deployment,
        "performance_target": performance,
        "estimated_complexity": "medium",
        "key_features": [],
        "recommended_patterns": ["REST API", "Repository Pattern"],
        "potential_challenges": []
    }


def get_learning_recommendations(requirements: str, language: str = "python") -> Dict[str, Any]:
    """Get recommendations based on past learning"""
    from src.memory.memory_store import memory_store
    
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
    bug_patterns = memory_store.search_bug_patterns(requirements, language=language, limit=5)
    recommendations["pitfalls"].extend([
        f"Avoid {p['bug_type']}: {p['fix']}" for p in bug_patterns
    ])
    
    # Search for architecture patterns
    architectures = memory_store.search_architectures(requirements, limit=3)
    recommendations["architecture"] = architectures
    
    return recommendations


def get_default_value(field: str) -> Any:
    """Get default value for plan fields"""
    defaults = {
        "requirements": "",
        "architecture": "monolithic",
        "language": "python",
        "framework": "fastapi",
        "database": "postgresql",
        "testing_strategy": "unit/integration",
        "deployment_strategy": "docker",
        "performance_target": "balanced",
        "estimated_complexity": "medium",
        "key_features": [],
        "recommended_patterns": [],
        "potential_challenges": []
    }
    return defaults.get(field, None)


def refine_plan(plan: Dict[str, Any], feedback: str) -> Dict[str, Any]:
    """Refine a plan based on feedback"""
    
    if has_llm_configured():
        try:
            llm = create_llm_client(
                config.llm_provider,
                config.openai_api_key or config.anthropic_api_key,
                config.openai_model if config.llm_provider == "openai" else config.anthropic_model
            )
            
            prompt = f"""Refine this project plan based on the feedback:

ORIGINAL PLAN:
{json.dumps(plan, indent=2)}

FEEDBACK:
{feedback}

Return the refined plan as JSON with the same structure as the original."""
            
            refined = llm.generate_json(prompt, "You are an expert software architect. Refine plans based on feedback.")
            return refined
        except:
            pass
    
    # Fallback: just append feedback to challenges
    plan["potential_challenges"].append(f"Feedback noted: {feedback}")
    return plan
