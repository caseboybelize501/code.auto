from src.bootstrap.toolchain_scanner import scan_toolchain
from src.bootstrap.dependency_scanner import scan_dependencies
from src.bootstrap.model_scanner import scan_models
from src.bootstrap.system_profile import create_system_profile

def scan_system():
    print("Starting system scan...")
    
    # Scan toolchain
    toolchain = scan_toolchain()
    
    # Scan dependencies
    dependencies = scan_dependencies()
    
    # Scan models
    models = scan_models()
    
    # Create system profile
    profile = create_system_profile(toolchain, dependencies, models)
    
    print("System scan complete.")
    return profile
