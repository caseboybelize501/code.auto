import os
import hashlib

def scan_models():
    models = {
        "gguf": [],
        "inference_servers": []
    }
    
    # Scan GGUF models
    try:
        model_dir = "/models"
        if os.path.exists(model_dir):
            for file in os.listdir(model_dir):
                if file.endswith(".gguf"):
                    file_path = os.path.join(model_dir, file)
                    with open(file_path, "rb") as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    models["gguf"].append({
                        "name": file,
                        "path": file_path,
                        "sha256": file_hash
                    })
    except Exception as e:
        pass
    
    # Scan inference servers
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name']):
            if 'inference' in proc.info['name'] or 'llm' in proc.info['name']:
                models["inference_servers"].append(proc.info)
    except Exception as e:
        pass
    
    return models
