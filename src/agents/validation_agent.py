"""Validation Agent - Validates generated code against requirements"""

import re
from typing import Dict, List, Any


def validate_code_against_plan(files: List[Dict[str, str]], plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that generated code implements the plan requirements.
    
    Args:
        files: List of generated files
        plan: Project plan with requirements and key features
        
    Returns:
        Validation results with pass/fail status and issues
    """
    result = {
        "passed": True,
        "issues": [],
        "warnings": [],
        "coverage": {
            "features_implemented": 0,
            "features_total": len(plan.get("key_features", [])),
            "models_found": [],
            "endpoints_found": []
        }
    }
    
    # Combine all file contents for analysis
    all_code = ""
    for file_info in files:
        all_code += file_info.get("content", "") + "\n"
    
    # Check for domain-specific models
    key_features = plan.get("key_features", [])
    requirements = plan.get("requirements", "").lower()
    
    # Detect expected models from requirements
    expected_models = _extract_expected_models(requirements, key_features)
    found_models = _find_models_in_code(all_code)
    
    # Check if expected models are present
    for expected in expected_models:
        found = any(expected.lower() in model.lower() for model in found_models)
        if not found:
            result["issues"].append(f"Expected model '{expected}' not found in generated code")
            result["passed"] = False
        else:
            result["coverage"]["models_found"].append(expected)
    
    # Check for generic "Item" model when domain-specific is needed
    if "class Item(BaseModel)" in all_code and not _is_item_appropriate(requirements):
        result["warnings"].append(
            "Generic 'Item' model detected. Consider using domain-specific models "
            f"like {', '.join(expected_models[:3])} based on requirements."
        )
    
    # Check for key features implementation
    features_found = []
    for feature in key_features:
        feature_keywords = _extract_feature_keywords(feature)
        if any(keyword.lower() in all_code.lower() for keyword in feature_keywords):
            features_found.append(feature)
    
    result["coverage"]["features_implemented"] = len(features_found)
    result["coverage"]["features_total"] = len(key_features)
    
    if key_features:
        coverage_pct = len(features_found) / len(key_features) * 100
        if coverage_pct < 50:
            result["issues"].append(
                f"Only {len(features_found)}/{len(key_features)} key features detected in code. "
                f"Missing: {', '.join(set(key_features) - set(features_found))}"
            )
            result["passed"] = False
    
    # Find endpoints
    result["coverage"]["endpoints_found"] = _find_endpoints_in_code(all_code)
    
    return result


def _extract_expected_models(requirements: str, key_features: List[str]) -> List[str]:
    """Extract expected model names from requirements"""
    models = []
    
    # Domain-specific model mapping
    if any(word in requirements for word in ["recipe", "food", "meal", "ingredient"]):
        models.extend(["Recipe", "Ingredient"])
    if any(word in requirements for word in ["task", "todo", "assignment"]):
        models.extend(["Task", "User"])
    if any(word in requirements for word in ["product", "shop", "catalog", "inventory"]):
        models.extend(["Product", "Category", "Order"])
    if any(word in requirements for word in ["user", "auth", "login", "register"]):
        models.extend(["User", "Token"])
    if any(word in requirements for word in ["chat", "message", "conversation"]):
        models.extend(["Message", "Room", "Conversation"])
    if any(word in requirements for word in ["event", "booking", "ticket"]):
        models.extend(["Event", "Booking", "Ticket"])
    if any(word in requirements for word in ["file", "document", "storage"]):
        models.extend(["File", "Document", "Folder"])
    
    # Extract from key features
    for feature in key_features:
        feature_lower = feature.lower()
        if "authentication" in feature_lower and "User" not in models:
            models.append("User")
        if "review" in feature_lower and "Review" not in models:
            models.append("Review")
        if "payment" in feature_lower and "Payment" not in models:
            models.append("Payment")
    
    return models if models else ["Item"]  # Default to Item if no domain detected


def _find_models_in_code(code: str) -> List[str]:
    """Find all model classes in the code"""
    models = []
    
    # Look for Pydantic models
    pydantic_pattern = r'class\s+(\w+)\s*\(\s*(BaseModel|pydantic\.BaseModel)\s*\)'
    matches = re.findall(pydantic_pattern, code)
    models.extend([match[0] for match in matches])
    
    # Look for SQLAlchemy models
    sqlalchemy_pattern = r'class\s+(\w+)\s*\(\s*db\.Model|declarative_base'
    matches = re.findall(sqlalchemy_pattern, code)
    models.extend(matches)
    
    return models


def _find_endpoints_in_code(code: str) -> List[str]:
    """Find API endpoints in the code"""
    endpoints = []
    
    # Look for FastAPI/Flask route decorators
    patterns = [
        r'@app\.get\(["\']([^"\']+)["\']',
        r'@app\.post\(["\']([^"\']+)["\']',
        r'@app\.put\(["\']([^"\']+)["\']',
        r'@app\.delete\(["\']([^"\']+)["\']',
        r'@app\.patch\(["\']([^"\']+)["\']',
        r'@router\.get\(["\']([^"\']+)["\']',
        r'@router\.post\(["\']([^"\']+)["\']',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, code)
        endpoints.extend(matches)
    
    return list(set(endpoints))


def _extract_feature_keywords(feature: str) -> List[str]:
    """Extract keywords from a feature description"""
    # Map common feature terms to code keywords
    keyword_map = {
        "authentication": ["auth", "login", "register", "jwt", "token", "password"],
        "authorization": ["permission", "role", "access", "admin"],
        "crud": ["create", "read", "update", "delete", "post", "get", "put", "delete"],
        "search": ["search", "filter", "query", "find"],
        "pagination": ["page", "limit", "offset", "skip"],
        "validation": ["validate", "validator", "check", "verify"],
        "notification": ["notify", "email", "send", "alert"],
        "upload": ["upload", "file", "image", "multipart"],
        "export": ["export", "download", "csv", "pdf"],
        "import": ["import", "parse", "upload"],
        "analytics": ["analytics", "stats", "metrics", "report"],
        "cache": ["cache", "redis", "memo"],
    }
    
    keywords = []
    feature_lower = feature.lower()
    
    for term, kw_list in keyword_map.items():
        if term in feature_lower:
            keywords.extend(kw_list)
    
    # Also add keywords from the feature itself
    keywords.extend(feature_lower.split())
    
    return keywords


def _is_item_appropriate(requirements: str) -> bool:
    """Check if generic 'Item' model is appropriate for the requirements"""
    # Item is only appropriate for very generic requirements
    appropriate_for = ["item", "generic", "simple", "basic", "starter"]
    return any(word in requirements for word in appropriate_for)


def validate_syntax(files: List[Dict[str, str]], language: str = "python") -> Dict[str, Any]:
    """
    Validate syntax of generated code.
    
    Args:
        files: List of generated files
        language: Programming language
        
    Returns:
        Validation results
    """
    result = {
        "passed": True,
        "errors": [],
        "warnings": []
    }
    
    for file_info in files:
        filepath = file_info.get("path", file_info.get("name", "unknown"))
        content = file_info.get("content", "")
        
        # Skip non-Python files
        if language == "python" and not filepath.endswith(".py"):
            continue
            
        if language == "python":
            try:
                compile(content, filepath, "exec")
            except SyntaxError as e:
                result["passed"] = False
                result["errors"].append(f"Syntax error in {filepath}: {e.msg} at line {e.lineno}")
            except Exception as e:
                result["warnings"].append(f"Warning in {filepath}: {str(e)}")
    
    return result
