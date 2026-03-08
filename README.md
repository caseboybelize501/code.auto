# 🤖 JARVIS - Automated Software Development System

An automated software development framework that takes project requirements and automatically plans, generates, tests, builds, deploys, and learns from the process.

**Powered by your local llama.cpp** - No API keys needed for owner use. Commercial API support available for customer deployments.

## 🚀 New Features (v2.0)

- **🧠 RAG Self-Learning Layer** - Learns from every project using ChromaDB vector storage
- **📝 Code Tracking Manager** - Tracks all generated code artifacts with pattern detection
- **✅ Validation Agent** - Validates generated code against requirements before deployment
- **🎯 Domain-Aware Generation** - 15+ domain detectors for context-specific code generation
- **🔧 Graceful Error Handling** - Continues pipeline even when dependencies fail
- **📊 Enhanced Monitoring** - RAG learning stats integrated into responses

## Features

- **Local LLM Powered** - Uses your offline llama.cpp server (no API costs)
- **Smart Planning** - Analyzes requirements and creates optimal project architecture
- **Code Generation** - Generates production-ready code (local AI + built-in templates)
- **Automated Testing** - Runs pytest/jest tests with coverage reporting
- **Multi-Language Build** - Supports Python, Node.js, Rust, Go, and Java
- **Docker Deployment** - Automatically containerizes and deploys applications
- **Runtime Monitoring** - Collects performance metrics (latency, throughput, CPU, memory)
- **Debug Analysis** - Error analysis and fix suggestions
- **RAG Learning** - Stores and retrieves patterns from past projects
- **Code Tracking** - Automatic artifact tracking with snippet extraction

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start llama.cpp Server

Make sure your llama.cpp server is running:

```bash
# Example llama.cpp server command
llama-server -m your-model.gguf --port 8080 --ctx-size 8192
```

### 3. Run the API Server

```bash
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

That's it! No API keys needed.

### 4. Access the API

- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### 5. (Optional) Run Frontend

```bash
cd frontend
npm install
npm start
```

## Configuration

### Owner Use (Local llama.cpp)

Default configuration uses your local llama.cpp server:

```env
CODE_AUTO_LLM_PROVIDER=llama-cpp
CODE_AUTO_LOCAL_LLM_ENABLED=true
CODE_AUTO_LOCAL_LLM_URL=http://localhost:8080
CODE_AUTO_LOCAL_LLM_MODEL=local-model
```

### Customer Deployments (Commercial APIs)

For customers who want cloud-based AI:

```env
CODE_AUTO_LLM_PROVIDER=openai
CODE_AUTO_OPENAI_API_KEY=sk-...
```

Or:

```env
CODE_AUTO_LLM_PROVIDER=anthropic
CODE_AUTO_ANTHROPIC_API_KEY=sk-ant-...
```

## API Endpoints

### Start Project
```bash
POST /api/project/start
Content-Type: application/json

{
  "requirements": "Build a REST API for a todo application with user authentication"
}
```

### Get System Profile
```bash
GET /api/system/profile
```

### List Workspace Files
```bash
GET /api/workspace/files
```

### Get Memory Stats (includes RAG)
```bash
GET /api/memory/stats
```

## How It Works

When you start a project, JARVIS executes:

1. **RAG Context** - Retrieves similar projects and patterns from knowledge base
2. **Plan** - Analyzes requirements, creates architecture plan (local LLM)
3. **Generate Code** - Creates source files with RAG-augmented context
4. **Validate** - Validates generated code against requirements
5. **Generate Tests** - Creates test files
6. **Run Tests** - Executes test suite (pytest/jest)
7. **Build** - Installs dependencies, validates syntax
8. **Deploy** - Creates Docker container or runs locally
9. **Monitor** - Benchmarks latency, throughput, resource usage
10. **Debug** - Analyzes any failures (local LLM)
11. **Learn** - Stores patterns in RAG storage for future projects
12. **Track** - Tracks all code artifacts with metadata

## Supported Languages & Frameworks

| Language | Frameworks | Build Tools |
|----------|------------|-------------|
| Python | FastAPI, Flask, Django | pip, poetry |
| JavaScript | Express, NestJS | npm, yarn |
| TypeScript | NestJS, Express | npm, yarn |
| Rust | Actix, Axum | cargo |
| Go | Gin, Echo | go mod |
| Java | Spring Boot | Maven, Gradle |

## Domain Detection

JARVIS automatically detects project domains and generates appropriate models:

| Domain | Keywords | Generated Models |
|--------|----------|------------------|
| IoT | iot, sensor, telemetry, mqtt | Sensor, TelemetryData, Alert |
| Crypto | crypto, bitcoin, portfolio | Asset, Portfolio, Transaction |
| Healthcare | health, patient, doctor | Patient, Doctor, Appointment |
| E-commerce | product, shop, cart | Product, Category, Order, Review |
| Education | course, student, lms | Course, Student, Enrollment |
| Smart Home | automation, light, zigbee | Device, Scene, Automation |
| Marketplace | freelance, gig, bid | Freelancer, Project, Bid |
| Restaurant | restaurant, menu, table | MenuItem, Table, Order |
| Legal | legal, document, contract | Document, Template, Clause |
| Fleet | fleet, vehicle, gps | Vehicle, Driver, Trip |
| Recipe | recipe, ingredient, meal | Recipe, Ingredient, MealPlan |
| Task | task, project, todo | Task, User, Project |
| Streaming | stream, kafka, event | Stream, Event, Processor |
| SaaS | saas, tenant, subscription | Tenant, Subscription, Feature |
| General | (fallback) | Item (generic) |

## Project Structure

```
code.auto/
├── src/
│   ├── main.py                 # FastAPI application
│   ├── agents/
│   │   ├── code_agent.py       # Code generation with RAG
│   │   ├── test_agent.py       # Test execution
│   │   ├── build_agent.py      # Build pipeline
│   │   ├── deploy_agent.py     # Deployment
│   │   ├── validation_agent.py # Code validation ✨ NEW
│   │   └── ...
│   ├── learning/
│   │   └── rag_layer.py        # RAG self-learning ✨ NEW
│   ├── tracking/
│   │   └── code_tracker.py     # Code artifact tracking ✨ NEW
│   ├── planner/
│   │   └── dev_planner.py      # Project planning
│   └── ...
├── workspace/                  # Generated projects
├── .rag_store/                 # RAG knowledge base
└── scripts/
    └── batch_jobs.py           # Batch job runner
```

## RAG Learning System

The RAG (Retrieval-Augmented Generation) layer continuously learns from projects:

### Knowledge Collections
- **code_patterns** - Reusable code snippets
- **architectures** - Successful architecture patterns
- **bug_fixes** - Known issues and solutions
- **domain_patterns** - Domain-specific patterns
- **successful_projects** - Complete project references

### Storage
- **Primary:** ChromaDB vector store (`workspace/.rag_store/chroma.sqlite3`)
- **Fallback:** JSON file (`workspace/.rag_store/knowledge_base.json`)

## Batch Processing

Run multiple projects automatically:

```bash
python scripts/batch_jobs.py [count]
# Examples:
python scripts/batch_jobs.py 5      # Run 5 projects
python scripts/batch_jobs.py 10     # Run 10 projects
```

## Business Model

### Owner Use (You)
- Uses your local llama.cpp server
- No API costs
- Full privacy
- Unlimited usage

### Customer Deployments
- Option 1: Customer provides their own API keys
- Option 2: Customer uses local llama.cpp (recommended)
- Option 3: You provide API access (your choice)

## Development

### Run Tests
```bash
python tests/test_pipeline.py
```

### Test llama.cpp Connection
```bash
curl http://localhost:8080/health
```

### Run Batch Jobs
```bash
python scripts/batch_jobs.py 10
```

## Troubleshooting

### "llama.cpp server not responding"
- Make sure llama.cpp server is running
- Check the URL in `.env` (default: http://localhost:8080)
- Test: `curl http://localhost:8080/health`

### "Docker not available"
- JARVIS falls back to local deployment automatically

### "pytest not found"
- Install: `pip install pytest pytest-asyncio`

### "pydantic-core build failed"
- Upgrade pydantic: `pip install --upgrade pydantic>=2.6.0`
- Requires Python 3.13 compatible version

### RAG not learning
- Check ChromaDB: `pip install chromadb`
- Fallback storage works without ChromaDB

## Performance Benchmarks

Based on 30+ batch job runs:

| Metric | Value |
|--------|-------|
| Avg Time/Project | 58-68 seconds |
| Success Rate | 100% |
| Code Files/Project | 4-7 files |
| RAG Retrieval | <100ms |
| Domains Supported | 15+ |

## License

Proprietary source-available license. See [LICENSE](LICENSE) for details.

## Contact

For questions: casebelize501@icloud.com

## Changelog

### v2.0 (Latest)
- ✨ RAG Self-Learning Layer with ChromaDB
- ✨ Code Tracking Manager
- ✨ Validation Agent for code quality
- ✨ 15+ domain detectors
- ✨ Graceful error handling
- ✨ Python 3.13 compatibility
- ✨ Updated dependencies (pydantic>=2.6.0, fastapi>=0.109.0)

### v1.0
- Initial release
- Basic code generation
- Planning and deployment
- Testing support
