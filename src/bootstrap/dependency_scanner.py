import subprocess
import json

def scan_dependencies():
    dependencies = {
        "pip": [],
        "npm": [],
        "cargo": []
    }
    
    # Scan pip packages
    try:
        result = subprocess.check_output(["pip", "list"], stderr=subprocess.STDOUT, text=True)
        lines = result.split('\n')[2:]  # Skip header lines
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    dependencies["pip"].append({"name": parts[0], "version": parts[1]})
    except Exception as e:
        pass
    
    # Scan npm packages
    try:
        result = subprocess.check_output(["npm", "list"], stderr=subprocess.STDOUT, text=True)
        lines = result.split('\n')
        for line in lines:
            if '└─' in line or '├─' in line:
                parts = line.split()
                if len(parts) >= 2:
                    dependencies["npm"].append({"name": parts[1], "version": parts[2]})
    except Exception as e:
        pass
    
    # Scan cargo packages
    try:
        result = subprocess.check_output(["cargo", "install", "--list"], stderr=subprocess.STDOUT, text=True)
        lines = result.split('\n')
        for line in lines:
            if ' ' in line and not line.startswith(' '):
                parts = line.split()
                dependencies["cargo"].append({"name": parts[0], "version": parts[1]})
    except Exception as e:
        pass
    
    return dependencies
