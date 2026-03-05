import subprocess
import json

def scan_toolchain():
    toolchain = {
        "compilers": {},
        "build_systems": [],
        "package_managers": [],
        "container_runtimes": [],
        "benchmarking_tools": [],
        "test_frameworks": []
    }
    
    # Scan compilers
    try:
        gcc_version = subprocess.check_output(["gcc", "--version"], stderr=subprocess.STDOUT, text=True)
        toolchain["compilers"]["gcc"] = gcc_version.split('\n')[0]
    except Exception as e:
        pass
    
    try:
        clang_version = subprocess.check_output(["clang", "--version"], stderr=subprocess.STDOUT, text=True)
        toolchain["compilers"]["clang"] = clang_version.split('\n')[0]
    except Exception as e:
        pass
    
    try:
        rustc_version = subprocess.check_output(["rustc", "--version"], stderr=subprocess.STDOUT, text=True)
        toolchain["compilers"]["rustc"] = rustc_version.split('\n')[0]
    except Exception as e:
        pass
    
    # Scan build systems
    build_systems = ["cmake", "make", "ninja", "cargo", "gradle"]
    for bs in build_systems:
        try:
            subprocess.check_output([bs, "--version"], stderr=subprocess.STDOUT, text=True)
            toolchain["build_systems"].append(bs)
        except Exception as e:
            pass
    
    # Scan package managers
    package_managers = ["pip", "npm", "cargo", "go"]
    for pm in package_managers:
        try:
            subprocess.check_output([pm, "--version"], stderr=subprocess.STDOUT, text=True)
            toolchain["package_managers"].append(pm)
        except Exception as e:
            pass
    
    # Scan container runtimes
    container_runtimes = ["docker", "podman"]
    for cr in container_runtimes:
        try:
            subprocess.check_output([cr, "--version"], stderr=subprocess.STDOUT, text=True)
            toolchain["container_runtimes"].append(cr)
        except Exception as e:
            pass
    
    # Scan benchmarking tools
    benchmarking_tools = ["locust", "wrk"]
    for bt in benchmarking_tools:
        try:
            subprocess.check_output([bt, "--version"], stderr=subprocess.STDOUT, text=True)
            toolchain["benchmarking_tools"].append(bt)
        except Exception as e:
            pass
    
    # Scan test frameworks
    test_frameworks = ["pytest", "jest", "go test", "cargo test"]
    for tf in test_frameworks:
        try:
            subprocess.check_output([tf], stderr=subprocess.STDOUT, text=True)
            toolchain["test_frameworks"].append(tf)
        except Exception as e:
            pass
    
    return toolchain
