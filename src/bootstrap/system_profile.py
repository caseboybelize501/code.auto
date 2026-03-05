import json

def create_system_profile(toolchain, dependencies, models):
    profile = {
        "toolchain": toolchain,
        "dependencies": dependencies,
        "models": models,
        "timestamp": "2028-01-01T00:00:00Z"
    }
    
    # Validate system
    if not validate_system(profile):
        raise Exception("System validation failed")
    
    return profile

def validate_system(profile):
    # Check that at least one compiler is available
    if not profile["toolchain"]["compilers"]:
        return False
    
    # Check that at least one build system is available
    if not profile["toolchain"]["build_systems"]:
        return False
    
    # Check that at least one package manager is available
    if not profile["toolchain"]["package_managers"]:
        return False
    
    return True
