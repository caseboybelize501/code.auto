"""Debug Agent - LLM-powered error analysis and fix generation"""

import os
import re
import json
from typing import Dict, List, Any, Optional
from config import config

from src.llm.client import create_llm_client


def debug_failure(logs: str, error_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Analyze failure logs and generate fix recommendations.
    
    Args:
        logs: Error logs from tests or runtime
        error_context: Additional context about the error
        
    Returns:
        Debug results with root cause, fix, and confidence
    """
    result = {
        "root_cause": "Unknown",
        "fix": "Review error logs manually",
        "confidence": 0.0,
        "regression_risk": 1.0,
        "error_type": "unknown",
        "affected_files": [],
        "suggested_changes": [],
        "logs": ""
    }
    
    try:
        # Parse error logs
        parsed_errors = parse_error_logs(logs)
        
        # Try LLM-powered analysis if available
        if has_llm_configured():
            llm_result = analyze_with_llm(logs, parsed_errors)
            result.update(llm_result)
        else:
            # Fallback to rule-based analysis
            rule_result = analyze_with_rules(logs, parsed_errors)
            result.update(rule_result)
        
        # Generate fix patches
        if result["affected_files"]:
            patches = generate_fix_patches(result)
            result["suggested_changes"] = patches
        
    except Exception as e:
        result["root_cause"] = f"Debug analysis failed: {str(e)}"
        result["logs"] = logs[-500:]  # Last 500 chars
    
    return result


def parse_error_logs(logs: str) -> List[Dict[str, Any]]:
    """Parse error logs into structured format"""
    
    errors = []
    
    # Python traceback pattern
    traceback_pattern = re.compile(
        r'Traceback \(most recent call last\):.*?File "(.+?)", line (\d+).*?\n(\w+Error): (.+?)(?=\n\n|\Z)',
        re.DOTALL
    )
    
    for match in traceback_pattern.finditer(logs):
        errors.append({
            "type": "python_traceback",
            "file": match.group(1),
            "line": int(match.group(2)),
            "error_type": match.group(3),
            "message": match.group(4).strip()
        })
    
    # Pytest failure pattern
    pytest_pattern = re.compile(
        r'FAILED.*?(test_.+?)::(.+?) - (.+?)(?=\n\n|\Z)',
        re.DOTALL
    )
    
    for match in pytest_pattern.finditer(logs):
        errors.append({
            "type": "pytest_failure",
            "test_file": match.group(1),
            "test_name": match.group(2),
            "message": match.group(3).strip()
        })
    
    # Generic error pattern
    generic_pattern = re.compile(r'(Error|Exception|Failed|FAILED):\s*(.+?)(?=\n|$)')
    
    for match in generic_pattern.finditer(logs):
        errors.append({
            "type": "generic",
            "error_type": match.group(1),
            "message": match.group(2).strip()
        })
    
    # Syntax error pattern
    syntax_pattern = re.compile(r'SyntaxError:\s*(.+?)\s*File "(.+?)", line (\d+)')
    
    for match in syntax_pattern.finditer(logs):
        errors.append({
            "type": "syntax_error",
            "message": match.group(1),
            "file": match.group(2),
            "line": int(match.group(3))
        })
    
    return errors


def has_llm_configured() -> bool:
    """Check if LLM is available (local llama.cpp or cloud)"""
    from config import config
    
    # Check local llama.cpp
    if config.local_llm_enabled:
        return True
    
    # Check cloud providers
    return (config.llm_provider == "openai" and config.openai_api_key) or \
           (config.llm_provider == "anthropic" and config.anthropic_api_key)


def analyze_with_llm(logs: str, parsed_errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Use LLM to analyze errors and suggest fixes (local or cloud)"""

    try:
        from config import config
        from src.llm.client import create_llm_client, check_llama_cpp_available
        
        # Determine which client to use
        if config.local_llm_enabled:
            if check_llama_cpp_available(config.local_llm_base_url):
                llm = create_llm_client(
                    "llama-cpp",
                    base_url=config.local_llm_base_url,
                    model=config.local_llm_model,
                    context_length=config.local_llm_context_length
                )
            else:
                raise RuntimeError("llama.cpp not available")
        elif config.llm_provider == "openai" and config.openai_api_key:
            llm = create_llm_client("openai", config.openai_api_key, config.openai_model)
        elif config.llm_provider == "anthropic" and config.anthropic_api_key:
            llm = create_llm_client("anthropic", config.anthropic_api_key, config.anthropic_model)
        else:
            raise RuntimeError("No LLM configured")
        
        system_prompt = """You are an expert software debugger. Analyze error logs and provide:
1. Root cause analysis
2. Specific fix recommendations
3. Code patches if applicable
4. Confidence level (0-1)
5. Regression risk (0-1)

Be specific and actionable. Reference exact file names and line numbers."""

        prompt = f"""Analyze these error logs and provide a structured fix:

ERROR LOGS:
{logs[:5000]}  # Truncate to avoid token limits

PARSED ERRORS:
{json.dumps(parsed_errors, indent=2)}

Respond with JSON in this exact format:
{{
    "root_cause": "Clear explanation of what caused the error",
    "error_type": "classification of error (syntax, runtime, logic, etc)",
    "affected_files": ["list", "of", "files"],
    "fix": "Step-by-step fix description",
    "code_fix": {{
        "file": "path/to/file.py",
        "original": "original code",
        "replacement": "fixed code"
    }},
    "confidence": 0.85,
    "regression_risk": 0.2
}}"""

        response = llm.generate_json(prompt, system_prompt)
        
        return {
            "root_cause": response.get("root_cause", "Unknown"),
            "error_type": response.get("error_type", "unknown"),
            "affected_files": response.get("affected_files", []),
            "fix": response.get("fix", "Manual review required"),
            "confidence": response.get("confidence", 0.5),
            "regression_risk": response.get("regression_risk", 0.5),
            "suggested_changes": [response.get("code_fix")] if response.get("code_fix") else []
        }
        
    except Exception as e:
        return {
            "root_cause": f"LLM analysis failed: {str(e)}",
            "error_type": "analysis_error",
            "affected_files": [],
            "fix": "Manual debugging required",
            "confidence": 0.3,
            "regression_risk": 0.5,
            "suggested_changes": []
        }


def analyze_with_rules(logs: str, parsed_errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Rule-based error analysis (fallback when LLM unavailable)"""
    
    result = {
        "root_cause": "",
        "error_type": "unknown",
        "affected_files": [],
        "fix": "",
        "confidence": 0.5,
        "regression_risk": 0.5,
        "suggested_changes": []
    }
    
    # Check for common error patterns
    logs_lower = logs.lower()
    
    if "module not found" in logs_lower or "importerror" in logs_lower:
        result.update({
            "root_cause": "Missing dependency - a required Python module is not installed",
            "error_type": "dependency_error",
            "fix": "Add the missing module to requirements.txt and run: pip install -r requirements.txt",
            "confidence": 0.9,
            "regression_risk": 0.1
        })
        
    elif "syntaxerror" in logs_lower:
        result.update({
            "root_cause": "Syntax error in code - invalid Python syntax",
            "error_type": "syntax_error",
            "fix": "Review the indicated line and fix the syntax error. Common causes: missing colons, unmatched parentheses, incorrect indentation",
            "confidence": 0.95,
            "regression_risk": 0.1
        })
        
    elif "nameerror" in logs_lower:
        result.update({
            "root_cause": "Undefined variable or function - a name is used but not defined",
            "error_type": "name_error",
            "fix": "Define the missing variable/function or check for typos in the name",
            "confidence": 0.85,
            "regression_risk": 0.2
        })
        
    elif "attributeerror" in logs_lower:
        result.update({
            "root_cause": "Attribute error - accessing a non-existent attribute or method",
            "error_type": "attribute_error",
            "fix": "Check that the object has the attribute you're trying to access. May need to initialize the object differently",
            "confidence": 0.85,
            "regression_risk": 0.2
        })
        
    elif "keyerror" in logs_lower:
        result.update({
            "root_cause": "Key error - accessing a dictionary key that doesn't exist",
            "error_type": "key_error",
            "fix": "Use .get() method with default value or check if key exists before accessing",
            "confidence": 0.9,
            "regression_risk": 0.15
        })
        
    elif "indexerror" in logs_lower:
        result.update({
            "root_cause": "Index error - accessing a list/tuple index that's out of range",
            "error_type": "index_error",
            "fix": "Check list bounds before accessing. Use len() to verify index is valid",
            "confidence": 0.9,
            "regression_risk": 0.15
        })
        
    elif "typeerror" in logs_lower:
        result.update({
            "root_cause": "Type error - operation performed on incompatible types",
            "error_type": "type_error",
            "fix": "Ensure operands are of compatible types. Add type conversion if needed",
            "confidence": 0.8,
            "regression_risk": 0.25
        })
        
    elif "file not found" in logs_lower or "no such file" in logs_lower:
        result.update({
            "root_cause": "File not found - trying to access a file that doesn't exist",
            "error_type": "file_error",
            "fix": "Check the file path is correct. Ensure the file exists before trying to read it",
            "confidence": 0.9,
            "regression_risk": 0.1
        })
        
    elif "connection refused" in logs_lower or "connection error" in logs_lower:
        result.update({
            "root_cause": "Connection error - unable to connect to a service or database",
            "error_type": "connection_error",
            "fix": "Check that the target service is running and the connection URL/port is correct",
            "confidence": 0.8,
            "regression_risk": 0.2
        })
        
    elif "timeout" in logs_lower:
        result.update({
            "root_cause": "Timeout error - operation took too long to complete",
            "error_type": "timeout_error",
            "fix": "Increase timeout value or optimize the slow operation",
            "confidence": 0.75,
            "regression_risk": 0.3
        })
        
    elif "assertion" in logs_lower:
        result.update({
            "root_cause": "Assertion failure - a test assertion did not evaluate to True",
            "error_type": "assertion_error",
            "fix": "Review the failing test and the code under test. Either the test expectation or the implementation needs to be corrected",
            "confidence": 0.8,
            "regression_risk": 0.3
        })
        
    else:
        # Generic fallback
        if parsed_errors:
            error = parsed_errors[0]
            result.update({
                "root_cause": error.get("message", "Unknown error"),
                "error_type": error.get("error_type", "unknown"),
                "affected_files": [error.get("file", "")] if error.get("file") else [],
                "fix": "Review the error message and stack trace to identify the issue",
                "confidence": 0.5,
                "regression_risk": 0.5
            })
        else:
            result.update({
                "root_cause": "Unable to determine root cause from logs",
                "error_type": "unknown",
                "fix": "Manual debugging required. Review logs carefully",
                "confidence": 0.3,
                "regression_risk": 0.5
            })
    
    return result


def generate_fix_patches(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate code patches for the fix"""
    
    patches = []
    
    for file_path in result.get("affected_files", []):
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                
                patches.append({
                    "file": file_path,
                    "action": "review",
                    "content": content[:1000]  # First 1000 chars for context
                })
            except:
                pass
    
    return patches


def apply_fix(patch: Dict[str, Any]) -> bool:
    """Apply a code fix patch"""
    
    file_path = patch.get("file")
    if not file_path or not os.path.exists(file_path):
        return False
    
    try:
        # Read original
        with open(file_path, "r") as f:
            content = f.read()
        
        # Apply replacement if provided
        if "original" in patch and "replacement" in patch:
            content = content.replace(patch["original"], patch["replacement"])
        
        # Write back
        with open(file_path, "w") as f:
            f.write(content)
        
        return True
        
    except Exception as e:
        print(f"Failed to apply fix: {e}")
        return False


def reproduce_error(error_context: Dict[str, Any]) -> Dict[str, Any]:
    """Attempt to reproduce an error for debugging"""
    
    result = {
        "reproducible": False,
        "steps": [],
        "error_output": ""
    }
    
    # This would run the code that caused the error
    # For now, just return the context
    result["steps"] = [
        "1. Set up the environment as described",
        "2. Run the failing test or operation",
        "3. Observe the error"
    ]
    
    return result
