import json

def generate_code(plan):
    # Consult architecture performance graph and algorithm library
    # Avoid known inefficient patterns
    
    files = [
        {
            "name": "main.py",
            "content": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef read_root():\n    return {'Hello': 'World'}"
        },
        {
            "name": "requirements.txt",
            "content": "fastapi==0.104.1\nuvicorn==0.24.0"
        }
    ]
    
    return files
