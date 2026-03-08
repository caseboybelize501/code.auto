"""Code Agent - AI-powered code generation"""

import os
import json
from typing import Dict, List, Any
from config import config

from src.llm.client import create_llm_client


def generate_code(plan: Dict[str, Any], rag_context: Dict = None) -> List[Dict[str, str]]:
    """
    Generate code files based on the project plan.

    Args:
        plan: Project plan with requirements, architecture, language, framework
        rag_context: Optional context from RAG layer with similar projects/patterns

    Returns:
        List of generated files with name and content
    """

    # Check if LLM is available
    if not has_llm():
        print("No LLM configured, using fallback code generation")
        return _generate_fallback_code(plan)

    try:
        llm = _get_llm()

        system_prompt = """You are an expert software engineer. Generate production-ready code based on the project plan.

CRITICAL RULES:
1. MUST create domain-specific models based on the requirements (NOT generic "Item" models)
2. MUST extract key entities from requirements (e.g., "Recipe", "Ingredient", "User", "Task")
3. MUST implement ALL key features listed in the plan
4. Follow best practices for the specified language and framework
5. Include proper error handling
6. Generate complete, working code (no placeholders or TODOs)
7. Include necessary imports and dependencies
8. Use meaningful variable and function names related to the domain

RESPONSE FORMAT:
Return ONLY valid JSON where keys are file paths and values are file contents."""

        # Build prompt with RAG context
        prompt = f"""Generate a COMPLETE project based on this plan:

REQUIREMENTS: {plan.get('requirements', 'Build a functional application')}

PLAN DETAILS:
- Architecture: {plan.get('architecture', 'monolithic')}
- Language: {plan.get('language', 'python')}
- Framework: {plan.get('framework', 'fastapi')}
- Database: {plan.get('database', 'postgresql')}
- Key Features: {', '.join(plan.get('key_features', []))}
- Recommended Patterns: {', '.join(plan.get('recommended_patterns', []))}
"""

        # Add RAG context if available
        if rag_context:
            if rag_context.get("projects"):
                prompt += f"\n\nSIMILAR SUCCESSFUL PROJECTS: {len(rag_context['projects'])} found\n"
                for proj in rag_context["projects"][:3]:
                    prompt += f"- {proj.get('architecture', 'Unknown')} for {proj.get('domain', 'unknown')}\n"
            
            if rag_context.get("patterns"):
                prompt += f"\n\nRELEVANT PATTERNS TO USE:\n"
                for pattern in rag_context["patterns"][:5]:
                    prompt += f"- {pattern.get('pattern', 'Unknown')} pattern\n"
            
            if rag_context.get("code_samples"):
                prompt += f"\n\n{len(rag_context['code_samples'])} code samples available for reference\n"

        prompt += """
EXAMPLE 1 - Recipe API:
If requirements are "Recipe API with ingredients and meal planning":
- Create models: Recipe, Ingredient, MealPlan, ShoppingList (NOT generic "Item")
- Create endpoints: /recipes, /ingredients, /meal-plans, /shopping-lists
- Include: nutritional calculation, dietary filtering, image upload handling

EXAMPLE 2 - Task Management:
If requirements are "Task management with authentication":
- Create models: User, Task, Role, Permission (NOT generic "Item")  
- Create endpoints: /auth, /users, /tasks, /roles
- Include: JWT auth, role-based access, task assignments

EXAMPLE 3 - E-commerce:
If requirements are "Product catalog with reviews":
- Create models: Product, Category, Review, Inventory (NOT generic "Item")
- Create endpoints: /products, /categories, /reviews, /inventory
- Include: search, filtering, pagination, ratings

NOW GENERATE for this project:
Create these files:
1. Main application file (main.py or app.py)
2. Configuration file (config.py)
3. Requirements/dependencies (requirements.txt)
4. README with setup instructions
5. Domain models (models.py or src/models/)
6. Service/business logic layer (services.py or src/services/)
7. Utility functions (utils.py)
8. Test file (tests/test_main.py)

Respond with a JSON object where keys are file paths and values are file contents.
DO NOT include markdown code fences. Return RAW JSON only."""

        files_dict = llm.generate_json(prompt, system_prompt, temperature=0.7)

        # Convert to list format
        files = []
        for filepath, content in files_dict.items():
            files.append({
                "name": filepath,
                "content": content,
                "path": filepath
            })

        # Write files to workspace
        written_files = _write_files(files)

        return written_files

    except Exception as e:
        # Fallback to basic generation
        print(f"LLM generation failed, using fallback: {e}")
        return _generate_fallback_code(plan)


def has_llm() -> bool:
    """Check if LLM is configured (local llama.cpp or cloud)"""
    from config import config
    
    # Check local llama.cpp first
    if config.local_llm_enabled:
        return True
    
    # Check cloud providers
    return (config.llm_provider == "openai" and config.openai_api_key) or \
           (config.llm_provider == "anthropic" and config.anthropic_api_key)


def _get_llm():
    """Get LLM client based on config - llama.cpp (local) or cloud APIs"""
    from config import config
    from src.llm.client import create_llm_client, check_llama_cpp_available
    
    # Use local llama.cpp if enabled
    if config.local_llm_enabled:
        try:
            # Check if server is actually running
            if check_llama_cpp_available(config.local_llm_base_url):
                return create_llm_client(
                    "llama-cpp",
                    base_url=config.local_llm_base_url,
                    model=config.local_llm_model,
                    context_length=config.local_llm_context_length
                )
            else:
                print(f"llama.cpp server not responding at {config.local_llm_base_url}")
        except Exception as e:
            print(f"llama.cpp not available: {e}")
    
    # Fall back to cloud providers
    if config.llm_provider == "openai" and config.openai_api_key:
        return create_llm_client("openai", config.openai_api_key, config.openai_model)
    elif config.llm_provider == "anthropic" and config.anthropic_api_key:
        return create_llm_client("anthropic", config.anthropic_api_key, config.anthropic_model)
    
    raise ValueError("No LLM available. Start llama.cpp server or configure API keys.")


def _write_files(files: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Write generated files to workspace"""
    workspace = config.work_dir
    os.makedirs(workspace, exist_ok=True)
    
    written_files = []
    for file_info in files:
        filepath = file_info.get("path", file_info["name"])
        full_path = os.path.join(workspace, filepath)
        
        # Create directories if needed
        dir_path = os.path.dirname(full_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # Write file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(file_info["content"])
        
        written_files.append({
            "name": file_info["name"],
            "content": file_info["content"],
            "path": filepath,
            "full_path": full_path
        })
    
    return written_files


def _generate_fallback_code(plan: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate basic fallback code when LLM is unavailable"""
    language = plan.get("language", "python")
    framework = plan.get("framework", "fastapi")
    requirements = plan.get("requirements", "").lower()
    key_features = plan.get("key_features", [])

    files = []

    if language == "python":
        if framework == "fastapi":
            files = _generate_fastapi_fallback(plan)
        elif framework == "flask":
            files = _generate_flask_fallback(plan)
        elif framework == "django":
            files = _generate_django_fallback(plan)

    # Write files
    return _write_files(files)


def _generate_fastapi_fallback(plan: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate FastAPI project with domain-specific models based on requirements"""
    requirements = plan.get("requirements", "").lower()
    key_features = plan.get("key_features", [])
    
    # Detect domain and create appropriate models
    domain_config = _detect_domain(requirements, key_features)
    
    return [
        {
            "name": "main.py",
            "path": "main.py",
            "content": _generate_main_py(plan, domain_config)
        },
        {
            "name": "models.py",
            "path": "models.py",
            "content": _generate_models_py(domain_config)
        },
        {
            "name": "requirements.txt",
            "path": "requirements.txt",
            "content": """fastapi>=0.109.0
uvicorn[standard]>=0.25.0
pydantic>=2.6.0
python-multipart>=0.0.7
pytest>=8.0.0
pytest-asyncio>=0.23.0
"""
        },
        {
            "name": "config.py",
            "path": "config.py",
            "content": """from pydantic import BaseModel
from typing import Optional

class Settings(BaseModel):
    app_name: str = "Auto-Generated API"
    debug: bool = True
    database_url: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()
"""
        },
        {
            "name": "utils.py",
            "path": "utils.py",
            "content": '''import logging
from functools import wraps
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def timing_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        logger.info(f"{func.__name__} executed in {time.time() - start:.3f}s")
        return result
    return wrapper
'''
        },
        {
            "name": "README.md",
            "path": "README.md",
            "content": f"""# {plan.get('requirements', 'Auto-Generated Project')}

Auto-generated FastAPI application.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

3. Access the API:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

{chr(10).join(f"- `{method} {path}` - {desc}" for method, path, desc in domain_config['endpoints'])}
"""
        },
        {
            "name": "tests/test_main.py",
            "path": "tests/test_main.py",
            "content": f'''"""Auto-generated tests for {plan.get("requirements", "API")}"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_list_{domain_config["primary_resource"]}s():
    response = client.get("/{domain_config["primary_resource"]}s")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_{domain_config["primary_resource"]}():
    data = {domain_config["test_data"]}
    response = client.post("/{domain_config["primary_resource"]}s", json=data)
    assert response.status_code == 201
    assert response.json()["id"] is not None
'''
        }
    ]


def _detect_domain(requirements: str, key_features: list) -> dict:
    """Detect domain from requirements and return configuration"""
    
    # IoT/Sensor domain
    if any(word in requirements for word in ["iot", "sensor", "telemetry", "device", "mqtt", "embedded"]):
        return {
            "domain": "iot",
            "primary_resource": "sensor",
            "models": [
                ("Sensor", ["id: Optional[int]", "name: str", "location: str", "status: str", "last_reading: Optional[float]"]),
                ("TelemetryData", ["id: Optional[int]", "sensor_id: int", "value: float", "unit: str", "timestamp: str"]),
                ("Alert", ["id: Optional[int]", "sensor_id: int", "severity: str", "message: str", "acknowledged: bool"]),
            ],
            "endpoints": [
                ("GET", "/sensors", "List all sensors"),
                ("GET", "/sensors/{id}", "Get sensor by ID"),
                ("POST", "/sensors/{id}/telemetry", "Submit telemetry data"),
                ("GET", "/alerts", "List alerts"),
                ("POST", "/alerts", "Create alert"),
            ],
            "test_data": '{"name": "Temp Sensor 1", "location": "Warehouse A", "status": "active"}'
        }
    
    # Crypto/Finance domain
    if any(word in requirements for word in ["crypto", "bitcoin", "ethereum", "portfolio", "trading", "exchange"]):
        return {
            "domain": "crypto",
            "primary_resource": "asset",
            "models": [
                ("Asset", ["id: Optional[int]", "symbol: str", "name: str", "current_price: float"]),
                ("Portfolio", ["id: Optional[int]", "user_id: int", "assets: List[dict]", "total_value: float"]),
                ("Transaction", ["id: Optional[int]", "asset_id: int", "type: str", "amount: float", "price: float"]),
            ],
            "endpoints": [
                ("GET", "/assets", "List all assets"),
                ("GET", "/portfolio", "Get portfolio"),
                ("POST", "/transactions", "Record transaction"),
                ("GET", "/prices", "Get current prices"),
            ],
            "test_data": '{"symbol": "BTC", "name": "Bitcoin", "current_price": 45000.00}'
        }
    
    # Healthcare/Medical domain
    if any(word in requirements for word in ["health", "medical", "patient", "doctor", "appointment", "hospital", "clinic"]):
        return {
            "domain": "healthcare",
            "primary_resource": "appointment",
            "models": [
                ("Patient", ["id: Optional[int]", "name: str", "date_of_birth: str", "contact: str"]),
                ("Doctor", ["id: Optional[int]", "name: str", "specialty: str", "availability: List[str]"]),
                ("Appointment", ["id: Optional[int]", "patient_id: int", "doctor_id: int", "datetime: str", "status: str"]),
            ],
            "endpoints": [
                ("GET", "/appointments", "List appointments"),
                ("POST", "/appointments", "Book appointment"),
                ("GET", "/patients", "List patients"),
                ("GET", "/doctors", "List doctors"),
            ],
            "test_data": '{"patient_id": 1, "doctor_id": 1, "datetime": "2024-01-15T10:00:00", "status": "scheduled"}'
        }
    
    # Supply Chain/Warehouse domain
    if any(word in requirements for word in ["warehouse", "inventory", "supply", "logistics", "shipment", "stock"]):
        return {
            "domain": "warehouse",
            "primary_resource": "inventory",
            "models": [
                ("Product", ["id: Optional[int]", "sku: str", "name: str", "category: str"]),
                ("Inventory", ["id: Optional[int]", "product_id: int", "quantity: int", "location: str"]),
                ("Shipment", ["id: Optional[int]", "inventory_id: int", "destination: str", "status: str"]),
            ],
            "endpoints": [
                ("GET", "/inventory", "List inventory"),
                ("POST", "/inventory", "Add inventory"),
                ("GET", "/shipments", "List shipments"),
                ("POST", "/shipments", "Create shipment"),
            ],
            "test_data": '{"product_id": 1, "quantity": 100, "location": "Warehouse A"}'
        }
    
    # Education/Learning domain
    if any(word in requirements for word in ["course", "student", "learning", "education", "school", "university", "lms"]):
        return {
            "domain": "education",
            "primary_resource": "course",
            "models": [
                ("Course", ["id: Optional[int]", "title: str", "description: str", "instructor: str"]),
                ("Student", ["id: Optional[int]", "name: str", "email: str", "enrolled_courses: List[int]"]),
                ("Enrollment", ["id: Optional[int]", "student_id: int", "course_id: int", "progress: float"]),
            ],
            "endpoints": [
                ("GET", "/courses", "List courses"),
                ("POST", "/courses", "Create course"),
                ("GET", "/students", "List students"),
                ("POST", "/enrollments", "Enroll student"),
            ],
            "test_data": '{"title": "Python 101", "description": "Learn Python basics", "instructor": "John Doe"}'
        }
    
    # Smart Home domain
    if any(word in requirements for word in ["smart home", "automation", "light", "thermostat", "lock", "zigbee", "z-wave"]):
        return {
            "domain": "smarthome",
            "primary_resource": "device",
            "models": [
                ("Device", ["id: Optional[int]", "name: str", "type: str", "status: str", "location: str"]),
                ("Scene", ["id: Optional[int]", "name: str", "devices: List[dict]", "trigger: str"]),
                ("Automation", ["id: Optional[int]", "name: str", "condition: str", "action: str"]),
            ],
            "endpoints": [
                ("GET", "/devices", "List devices"),
                ("PUT", "/devices/{id}", "Control device"),
                ("GET", "/scenes", "List scenes"),
                ("POST", "/automations", "Create automation"),
            ],
            "test_data": '{"name": "Living Room Light", "type": "light", "status": "on", "location": "Living Room"}'
        }
    
    # Freelance/Marketplace domain
    if any(word in requirements for word in ["freelance", "gig", "marketplace", "bid", "freelancer", "client"]):
        return {
            "domain": "marketplace",
            "primary_resource": "project",
            "models": [
                ("Freelancer", ["id: Optional[int]", "name: str", "skills: List[str]", "rating: float"]),
                ("Project", ["id: Optional[int]", "title: str", "description: str", "budget: float", "status: str"]),
                ("Bid", ["id: Optional[int]", "project_id: int", "freelancer_id: int", "amount: float", "proposal: str"]),
            ],
            "endpoints": [
                ("GET", "/projects", "List projects"),
                ("POST", "/projects", "Create project"),
                ("POST", "/bids", "Place bid"),
                ("GET", "/freelancers", "List freelancers"),
            ],
            "test_data": '{"title": "Build Website", "description": "Need a portfolio site", "budget": 2000, "status": "open"}'
        }
    
    # Restaurant/Food domain
    if any(word in requirements for word in ["restaurant", "food", "menu", "order", "table", "reservation", "dining"]):
        return {
            "domain": "restaurant",
            "primary_resource": "order",
            "models": [
                ("MenuItem", ["id: Optional[int]", "name: str", "description: str", "price: float", "category: str"]),
                ("Table", ["id: Optional[int]", "number: int", "capacity: int", "status: str"]),
                ("Order", ["id: Optional[int]", "table_id: int", "items: List[dict]", "total: float", "status: str"]),
            ],
            "endpoints": [
                ("GET", "/menu", "List menu items"),
                ("GET", "/tables", "List tables"),
                ("POST", "/orders", "Create order"),
                ("POST", "/reservations", "Book table"),
            ],
            "test_data": '{"table_id": 1, "items": [{"item_id": 1, "quantity": 2}], "total": 45.00, "status": "pending"}'
        }
    
    # Legal/Document domain
    if any(word in requirements for word in ["legal", "document", "contract", "agreement", "clause", "template"]):
        return {
            "domain": "legal",
            "primary_resource": "document",
            "models": [
                ("Document", ["id: Optional[int]", "title: str", "type: str", "content: str", "status: str"]),
                ("Template", ["id: Optional[int]", "name: str", "category: str", "fields: List[str]"]),
                ("Clause", ["id: Optional[int]", "title: str", "content: str", "category: str"]),
            ],
            "endpoints": [
                ("GET", "/documents", "List documents"),
                ("POST", "/documents", "Create document"),
                ("GET", "/templates", "List templates"),
                ("GET", "/clauses", "List clauses"),
            ],
            "test_data": '{"title": "Service Agreement", "type": "contract", "status": "draft"}'
        }
    
    # Fleet/Vehicle domain
    if any(word in requirements for word in ["fleet", "vehicle", "gps", "tracking", "driver", "route", "telematics"]):
        return {
            "domain": "fleet",
            "primary_resource": "vehicle",
            "models": [
                ("Vehicle", ["id: Optional[int]", "license_plate: str", "model: str", "status: str", "location: str"]),
                ("Driver", ["id: Optional[int]", "name: str", "license: str", "phone: str"]),
                ("Trip", ["id: Optional[int]", "vehicle_id: int", "driver_id: int", "route: str", "distance: float"]),
            ],
            "endpoints": [
                ("GET", "/vehicles", "List vehicles"),
                ("GET", "/vehicles/{id}/location", "Get vehicle location"),
                ("POST", "/trips", "Start trip"),
                ("GET", "/drivers", "List drivers"),
            ],
            "test_data": '{"license_plate": "ABC123", "model": "Ford Transit", "status": "active"}'
        }
    
    # Recipe/Food domain
    if any(word in requirements for word in ["recipe", "food", "meal", "ingredient", "cooking"]):
        return {
            "domain": "recipe",
            "primary_resource": "recipe",
            "models": [
                ("Recipe", ["id: Optional[int]", "title: str", "description: str", "prep_time: int", "cook_time: int", "servings: int", "instructions: List[str]"]),
                ("Ingredient", ["id: Optional[int]", "name: str", "quantity: float", "unit: str", "recipe_id: Optional[int]"]),
                ("MealPlan", ["id: Optional[int]", "name: str", "date: str", "recipes: List[int]"]),
            ],
            "endpoints": [
                ("GET", "/recipes", "List all recipes"),
                ("GET", "/recipes/{id}", "Get recipe by ID"),
                ("POST", "/recipes", "Create new recipe"),
                ("GET", "/ingredients", "List ingredients"),
                ("GET", "/meal-plans", "List meal plans"),
            ],
            "test_data": '{"title": "Pasta", "description": "Delicious pasta", "prep_time": 10, "cook_time": 20, "servings": 4, "instructions": ["Boil water", "Cook pasta"]}'
        }
    
    # Task/Project management domain
    if any(word in requirements for word in ["task", "project", "todo", "assignment", "work"]):
        return {
            "domain": "task",
            "primary_resource": "task",
            "models": [
                ("Task", ["id: Optional[int]", "title: str", "description: str", "status: str", "priority: str", "due_date: Optional[str]", "assigned_to: Optional[int]"]),
                ("User", ["id: Optional[int]", "username: str", "email: str", "role: str"]),
                ("Project", ["id: Optional[int]", "name: str", "description: str", "tasks: List[int]"]),
            ],
            "endpoints": [
                ("GET", "/tasks", "List all tasks"),
                ("GET", "/tasks/{id}", "Get task by ID"),
                ("POST", "/tasks", "Create new task"),
                ("PUT", "/tasks/{id}", "Update task"),
                ("DELETE", "/tasks/{id}", "Delete task"),
                ("GET", "/users", "List users"),
            ],
            "test_data": '{"title": "Complete report", "description": "Finish the quarterly report", "status": "pending", "priority": "high"}'
        }
    
    # E-commerce/Product domain
    elif any(word in requirements for word in ["product", "shop", "cart", "order", "inventory", "catalog"]):
        return {
            "domain": "product",
            "primary_resource": "product",
            "models": [
                ("Product", ["id: Optional[int]", "name: str", "description: str", "price: float", "category: str", "stock: int"]),
                ("Category", ["id: Optional[int]", "name: str", "parent_id: Optional[int]"]),
                ("Order", ["id: Optional[int]", "user_id: int", "products: List[dict]", "total: float", "status: str"]),
                ("Review", ["id: Optional[int]", "product_id: int", "rating: int", "comment: str", "user_id: int"]),
            ],
            "endpoints": [
                ("GET", "/products", "List all products"),
                ("GET", "/products/{id}", "Get product by ID"),
                ("POST", "/products", "Create new product"),
                ("GET", "/categories", "List categories"),
                ("POST", "/orders", "Create order"),
                ("GET", "/products/{id}/reviews", "Get product reviews"),
            ],
            "test_data": '{"name": "Laptop", "description": "High-performance laptop", "price": 999.99, "category": "Electronics", "stock": 50}'
        }
    
    # User/Auth domain
    elif any(word in requirements for word in ["user", "auth", "login", "register", "account"]):
        return {
            "domain": "user",
            "primary_resource": "user",
            "models": [
                ("User", ["id: Optional[int]", "username: str", "email: str", "hashed_password: str", "is_active: bool", "role: str"]),
                ("Token", ["access_token: str", "token_type: str"]),
                ("UserProfile", ["id: Optional[int]", "user_id: int", "bio: str", "avatar: Optional[str]"]),
            ],
            "endpoints": [
                ("POST", "/auth/register", "Register new user"),
                ("POST", "/auth/login", "Login user"),
                ("GET", "/users", "List all users"),
                ("GET", "/users/{id}", "Get user by ID"),
                ("PUT", "/users/{id}", "Update user"),
            ],
            "test_data": '{"username": "johndoe", "email": "john@example.com", "password": "securepass123"}'
        }
    
    # Chat/Messaging domain
    elif any(word in requirements for word in ["chat", "message", "conversation", "room"]):
        return {
            "domain": "message",
            "primary_resource": "message",
            "models": [
                ("Message", ["id: Optional[int]", "content: str", "sender_id: int", "room_id: int", "timestamp: str"]),
                ("Room", ["id: Optional[int]", "name: str", "members: List[int]", "is_private: bool"]),
                ("User", ["id: Optional[int]", "username: str", "status: str"]),
            ],
            "endpoints": [
                ("GET", "/rooms", "List all rooms"),
                ("GET", "/rooms/{id}/messages", "Get room messages"),
                ("POST", "/rooms/{id}/messages", "Send message"),
                ("GET", "/users", "List users"),
            ],
            "test_data": '{"content": "Hello!", "sender_id": 1, "room_id": 1}'
        }
    
    # Default fallback
    return {
        "domain": "generic",
        "primary_resource": "item",
        "models": [
            ("Item", ["id: Optional[int]", "name: str", "description: Optional[str]", "created_at: str"]),
        ],
        "endpoints": [
            ("GET", "/items", "List all items"),
            ("GET", "/items/{id}", "Get item by ID"),
            ("POST", "/items", "Create new item"),
        ],
        "test_data": '{"name": "Test Item", "description": "A test item"}'
    }


def _generate_main_py(plan: Dict[str, Any], domain_config: dict) -> str:
    """Generate main.py with domain-specific endpoints"""
    title = plan.get('requirements', 'Auto-Generated API').replace('"', '\\"')
    models = domain_config["models"]
    primary = domain_config["primary_resource"]
    
    # Generate model classes
    model_classes = ""
    for model_name, fields in models:
        model_classes += f"\nclass {model_name}(BaseModel):\n"
        for field in fields:
            model_classes += f"    {field}\n"
    
    # Generate in-memory storage
    storage = f"{primary}s_db = {{}}"
    
    # Generate endpoints
    endpoints_code = f'''
@app.get("/")
async def root():
    return Response(success=True, message="API is running", data={{"status": "healthy"}})


@app.get("/{primary}s", response_model=List[{models[0][0]}])
async def list_{primary}s():
    return list({primary}s_db.values())


@app.get("/{primary}s/{{item_id}}", response_model={models[0][0]})
async def get_{primary}(item_id: int):
    if item_id not in {primary}s_db:
        raise HTTPException(status_code=404, detail="{title} not found")
    return {primary}s_db[item_id]


@app.post("/{primary}s", response_model={models[0][0]}, status_code=201)
async def create_{primary}(item: {models[0][0]}):
    item_id = len({primary}s_db) + 1
    item.id = item_id
    {primary}s_db[item_id] = item
    return item


@app.put("/{primary}s/{{item_id}}", response_model={models[0][0]})
async def update_{primary}(item_id: int, item: {models[0][0]}):
    if item_id not in {primary}s_db:
        raise HTTPException(status_code=404, detail="{title} not found")
    item.id = item_id
    {primary}s_db[item_id] = item
    return item


@app.delete("/{primary}s/{{item_id}}")
async def delete_{primary}(item_id: int):
    if item_id not in {primary}s_db:
        raise HTTPException(status_code=404, detail="{title} not found")
    del {primary}s_db[item_id]
    return Response(success=True, message="{title} deleted")
'''
    
    return f'''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime

app = FastAPI(
    title="{title}",
    description="Auto-generated FastAPI application",
    version="1.0.0"
)

# Response models
class Response(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

# Domain models{model_classes}

# In-memory storage
{storage}

# Endpoints{endpoints_code}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''


def _generate_models_py(domain_config: dict) -> str:
    """Generate models.py with domain-specific Pydantic models"""
    models = domain_config["models"]
    
    model_classes = ""
    for model_name, fields in models:
        model_classes += f"\nclass {model_name}(BaseModel):\n"
        for field in fields:
            model_classes += f"    {field}\n"
        model_classes += "\n"
    
    return f'''"""Domain models for {domain_config["domain"]} API"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
{model_classes}
'''


def _generate_flask_fallback(plan: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate Flask project fallback"""
    return [
        {
            "name": "app.py",
            "path": "app.py",
            "content": f'''from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# In-memory storage
items = {{}}

@app.route("/")
def index():
    return jsonify({{"status": "healthy", "message": "{plan.get('requirements', 'Flask API')}"}})

@app.route("/items", methods=["GET"])
def get_items():
    return jsonify(list(items.values()))

@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    if item_id not in items:
        return jsonify({{"error": "Not found"}}), 404
    return jsonify(items[item_id])

@app.route("/items", methods=["POST"])
def create_item():
    data = request.json
    item_id = len(items) + 1
    item = {{"id": item_id, **data}}
    items[item_id] = item
    return jsonify(item), 201

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
'''
        },
        {
            "name": "requirements.txt",
            "path": "requirements.txt",
            "content": """flask==3.0.0
flask-cors==4.0.0
pytest==7.4.3
"""
        }
    ]


def _generate_django_fallback(plan: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate Django project fallback"""
    return [
        {
            "name": "manage.py",
            "path": "manage.py",
            "content": """#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django."
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
"""
        },
        {
            "name": "requirements.txt",
            "path": "requirements.txt",
            "content": """django==5.0.0
djangorestframework==3.14.0
pytest==7.4.3
pytest-django==4.7.0
"""
        }
    ]
