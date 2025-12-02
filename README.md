# 🤖 MCP Tool-Calling Agent

> **A production-ready AI Agent with autonomous tool selection and execution capabilities, built using Model Context Protocol (MCP) architecture.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange)](https://openai.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 🎬 Live Demo

![MCP Agent Demo](https://via.placeholder.com/800x400/667eea/ffffff?text=MCP+Agent+Demo+Screenshot)

**Quick Demo Commands:**
- `"Search for latest AI news"` → Web search with DuckDuckGo
- `"Calculate 15% of 280"` → Safe mathematical computation
- `"What's the weather in London?"` → Real-time weather data
- Upload a PDF → Intelligent document summarization
- `"List files in current directory"` → System information access

## 📋 Table of Contents

- [🎯 Project Overview](#-project-overview)
- [🏗️ Architecture](#️-architecture)  
- [🛠️ Tools & Features](#️-tools--features)
- [🚀 Quick Start](#-quick-start)
- [📦 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
- [🏃‍♂️ Running the Agent](#️-running-the-agent)
- [📝 Example Queries](#-example-queries)
- [📚 API Documentation](#-api-documentation)
- [🔧 Development](#-development)
- [🧪 Testing](#-testing)
- [📊 Monitoring](#-monitoring)
- [🚀 Deployment](#-deployment)
- [🗺️ Roadmap](#️-roadmap)
- [🤝 Contributing](#-contributing)

## 🎯 Project Overview

The **MCP Tool-Calling Agent** is a production-ready AI system that autonomously selects and executes tools based on user queries. Built following the Model Context Protocol (MCP) principles, it provides a robust foundation for AI-driven automation and intelligent task execution.

### What is MCP / Tool-Calling?

**Model Context Protocol (MCP)** is an architectural pattern that enables AI models to:
- **Autonomously select** appropriate tools for given tasks
- **Execute tools** with proper parameter validation
- **Chain multiple tools** for complex multi-step reasoning
- **Provide structured responses** with execution transparency

### Key Features

✨ **Autonomous Tool Selection** - LLM-powered decision making  
🔧 **6 Built-in Tools** - Search, Calculator, PDF, Weather, RAG, System  
🔄 **Multi-step Reasoning** - Handle complex queries requiring multiple tools  
🛡️ **Safety & Validation** - Comprehensive input validation and error handling  
🎨 **Modern UI** - Clean, responsive web interface  
🐳 **Docker Ready** - Easy deployment with Docker Compose  
📊 **Comprehensive Logging** - Detailed execution tracking  
🔌 **Extensible Architecture** - Easy to add new tools  

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ Query Input │ │ PDF Upload  │ │ Results View│          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
                      HTTP/REST API
                              │
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   /agent    │ │ /upload-pdf │ │   /tools    │          │
│  │   /health   │ │  /uploads   │ │   /docs     │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   MCP AGENT CORE                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              AGENT ORCHESTRATOR                     │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │   │
│  │  │Query Analysis│ │Multi-step   │ │Answer       │  │   │
│  │  │             │ │Execution    │ │Generation   │  │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                              │                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 LLM INTERFACE                       │   │
│  │  ┌─────────────┐ ┌─────────────┐                   │   │
│  │  │Tool Selection│ │Answer Gen   │                   │   │
│  │  │(GPT/Fallback)│ │(GPT/Fallback)│                 │   │
│  │  └─────────────┘ └─────────────┘                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                              │                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 TOOL MANAGER                        │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │   │
│  │  │Tool Registry│ │Validation   │ │Execution    │  │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      TOOL LAYER                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │Search Tool  │ │Calculator   │ │PDF Summarizer│          │
│  │DuckDuckGo   │ │Safe Math    │ │PyPDF2 + LLM │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │Weather Tool │ │  RAG Tool   │ │System Tool  │          │
│  │Open-Meteo   │ │FAISS+Sentence│ │psutil + OS  │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Tools & Features

### 🔍 1. Search Tool
- **Provider**: DuckDuckGo API
- **Capabilities**: Web search with top 5 results
- **Input**: Search query string
- **Output**: Titles, URLs, and snippets

**Example Tool Call JSON:**
```json
{
  "tool": "search_tool",
  "arguments": {
    "query": "latest artificial intelligence news",
    "num_results": 5
  }
}
```

### 🧮 2. Calculator Tool
- **Provider**: Safe AST-based Python evaluation
- **Capabilities**: Arithmetic, advanced math functions
- **Input**: Mathematical expressions
- **Output**: Calculated results with formatting

**Example Tool Call JSON:**
```json
{
  "tool": "calculator_tool", 
  "arguments": {
    "expression": "sqrt(16) + 25% of 80",
    "precision": 2
  }
}
```

### 📄 3. PDF Summarizer Tool
- **Provider**: PyPDF2 + OpenAI GPT
- **Capabilities**: Text extraction and intelligent summarization
- **Input**: PDF file path, summary preferences
- **Output**: Summary, key points, metadata

**Example Tool Call JSON:**
```json
{
  "tool": "pdf_summarizer_tool",
  "arguments": {
    "file_path": "/uploads/document.pdf",
    "summary_length": "medium",
    "focus_area": "key findings"
  }
}
```

### 🌤️ 4. Weather Tool  
- **Provider**: Open-Meteo API (free)
- **Capabilities**: Current weather and 3-day forecasts
- **Input**: Location name
- **Output**: Temperature, humidity, conditions, forecast

**Example Tool Call JSON:**
```json
{
  "tool": "weather_tool",
  "arguments": {
    "location": "London, UK",
    "include_forecast": true,
    "units": "celsius"
  }
}
```

### 🧠 5. RAG Tool (Retrieval-Augmented Generation)
- **Provider**: FAISS + Sentence Transformers + OpenAI
- **Capabilities**: Document search and Q&A
- **Input**: Questions about indexed documents  
- **Output**: Retrieved context + generated answers

**Example Tool Call JSON:**
```json
{
  "tool": "rag_tool",
  "arguments": {
    "question": "What are the main benefits of AI?",
    "top_k": 3,
    "generate_answer": true
  }
}
```

### 💻 6. System Tool
- **Provider**: psutil + OS modules
- **Capabilities**: System info, file operations, disk usage
- **Input**: Operation type and path
- **Output**: System metrics, file listings, metadata

**Example Tool Call JSON:**
```json
{
  "tool": "system_tool",
  "arguments": {
    "operation": "list_directory",
    "path": "/home/user/documents",
    "include_hidden": false
  }
}
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ 
- Docker (optional)
- OpenAI API Key (optional - fallback mode available)

### 1-Minute Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-tool-calling-agent.git
cd mcp-tool-calling-agent

# Copy environment file
cp .env.example .env
# Edit .env with your OpenAI API key (optional)

# Run with Docker (recommended)
docker-compose up --build

# Or run locally
pip install -r backend/requirements.txt
cd backend
python main.py
```

🎉 **Access the agent at**: http://localhost:8000

## 📦 Installation

### Option 1: Docker (Recommended)
```bash
# Clone repository
git clone https://github.com/yourusername/mcp-tool-calling-agent.git
cd mcp-tool-calling-agent

# Start with Docker Compose
docker-compose up --build
```

### Option 2: Local Development
```bash
# Clone repository  
git clone https://github.com/yourusername/mcp-tool-calling-agent.git
cd mcp-tool-calling-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Copy configuration
cp .env.example .env
```

## ⚙️ Configuration

### Environment Variables
Edit the `.env` file with your configuration:

```bash
# OpenAI Configuration (Optional)
OPENAI_API_KEY=your_openai_api_key_here

# Server Settings  
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info

# Tool Configuration
SEARCH_TOOL_ENABLED=true
CALCULATOR_TOOL_ENABLED=true
PDF_SUMMARIZER_TOOL_ENABLED=true
WEATHER_TOOL_ENABLED=true
RAG_TOOL_ENABLED=true  
SYSTEM_TOOL_ENABLED=true

# Agent Settings
MAX_RETRIES=3
RETRY_DELAY=1.0
AGENT_TIMEOUT=300
```

### Without OpenAI API Key
The agent includes **intelligent fallback logic** and works without OpenAI:
- Tool selection uses keyword-based heuristics
- Answer generation uses extractive summarization
- All core functionality remains available

## 🏃‍♂️ Running the Agent

### Development Mode
```bash
cd backend
python main.py
```

### Production Mode
```bash
# With Docker
docker-compose up -d

# Or with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Health Check
```bash
curl http://localhost:8000/health
```

## 📝 Example Queries

### Single Tool Examples

**🔍 Web Search:**
```
"Search for the latest developments in artificial intelligence"
```

**🧮 Calculations:**  
```
"Calculate the compound interest on $1000 at 5% for 3 years"
```

**🌤️ Weather:**
```  
"What's the weather forecast for Tokyo this week?"
```

**📄 PDF Analysis:**
```
"Summarize the main points from the uploaded research paper"
```

**💻 System Info:**
```
"Show me the files in my current directory"
```

### Multi-Step Reasoning Examples

**Complex Query 1:**
```
"Search for recent AI news and then calculate what 15% of the current Bitcoin price would be"
```

**Expected Agent Behavior:**
1. 🔍 Execute search_tool("recent AI news")  
2. 🧮 Execute calculator_tool("Bitcoin_price * 0.15")
3. 🧠 Generate combined answer with both results

**Complex Query 2:**  
```
"Summarize this PDF and then tell me the weather in the author's city"
```

**Expected Agent Behavior:**
1. 📄 Execute pdf_summarizer_tool(uploaded_file)
2. 🌤️ Execute weather_tool(extracted_city)  
3. 🧠 Combine PDF summary with weather info

### Error Handling Examples

**Invalid Input:**
```
"Calculate the square root of negative one hundred"
```
**Response:** Graceful error explanation with suggested alternatives

**Network Issues:**
```  
"Search for something" (when API is down)
```
**Response:** Fallback behavior with retry attempts

## 📚 API Documentation

### Core Endpoints

#### POST `/agent`
Process a query using the MCP agent.

**Request Body:**
```json
{
  "query": "Your question here",
  "context": {
    "uploaded_file": "path/to/file.pdf"
  }
}
```

**Response:**
```json
{
  "query": "Your question here", 
  "final_answer": "Generated response...",
  "tools_used": ["search_tool", "calculator_tool"],
  "steps": [
    "Retrieved available tools",
    "Selected 2 tool(s): search_tool, calculator_tool", 
    "Executing search_tool with arguments: {...}",
    "✓ search_tool completed successfully",
    "✓ Query processing completed successfully"
  ],
  "raw_outputs": [
    {
      "success": true,
      "tool_name": "search_tool",
      "results": [...],
      "timestamp": "2024-12-02T10:30:00Z"
    }
  ],
  "execution_time_seconds": 2.45,
  "success": true,
  "timestamp": "2024-12-02T10:30:00Z"
}
```

#### POST `/upload-pdf`
Upload a PDF file for processing.

**Request:** Multipart form data with PDF file

**Response:**
```json
{
  "success": true,
  "filename": "20241202_103000_document.pdf",
  "file_path": "/app/uploads/20241202_103000_document.pdf", 
  "size_bytes": 1048576,
  "upload_time": "2024-12-02T10:30:00Z"
}
```

#### GET `/tools`
Get information about available tools.

**Response:**
```json
{
  "success": true,
  "tools": [
    {
      "name": "search_tool",
      "description": "Search the web using DuckDuckGo",
      "input_schema": {...},
      "output_schema": {...}
    }
  ],
  "statistics": {
    "total_tools": 6,
    "tool_names": ["search_tool", "calculator_tool", ...]
  }
}
```

#### GET `/health`  
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-02T10:30:00Z",
  "agent_info": {
    "agent_status": "healthy",
    "llm_available": true,
    "tools_available": 6,
    "tool_list": ["search_tool", "calculator_tool", ...]
  }
}
```

### Interactive API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Development

### Project Structure
```
mcp-tool-calling-agent/
├── backend/                 # FastAPI backend
│   ├── main.py             # FastAPI application
│   ├── agent.py            # Core agent logic  
│   ├── llm.py              # LLM interface
│   ├── tool_manager.py     # Tool management
│   ├── tools/              # Individual tools
│   │   ├── search_tool.py
│   │   ├── calculator_tool.py
│   │   ├── pdf_summarizer.py
│   │   ├── weather_tool.py
│   │   ├── rag_tool.py
│   │   └── system_tool.py
│   ├── tests/              # Test files
│   ├── utils/              # Utility functions
│   └── requirements.txt    # Dependencies
├── frontend/               # Web UI
│   ├── index.html          # Main page
│   ├── styles.css          # Styling
│   └── app.js              # JavaScript logic
├── diagrams/               # Architecture diagrams
├── uploads/                # Uploaded files storage
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
├── .env.example            # Environment template
└── README.md               # This file
```

### Adding New Tools

1. **Create Tool Module** (`backend/tools/my_tool.py`):
```python
class MyTool:
    def __init__(self):
        self.name = "my_tool"
        self.description = "Description of what this tool does"
    
    def get_schema(self):
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {...},
            "output_schema": {...}
        }
    
    def execute(self, arguments):
        # Tool implementation
        return {
            "success": True,
            "result": "Tool output"
        }

my_tool = MyTool()
```

2. **Register Tool** (`backend/tool_manager.py`):
```python
from tools.my_tool import my_tool

def _register_tools(self):
    available_tools = [
        # ... existing tools
        my_tool,
    ]
```

3. **Update LLM Interface** (`backend/llm.py`):
Add keyword detection and fallback logic for your new tool.

### Code Style
```bash
# Format code
black backend/

# Lint code  
flake8 backend/

# Type checking
mypy backend/
```

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest backend/tests/

# Run with coverage
pytest --cov=backend backend/tests/
```

### Test Structure
```
backend/tests/
├── test_agent.py           # Agent core tests
├── test_tools.py           # Individual tool tests  
├── test_api.py             # API endpoint tests
├── conftest.py             # Test configuration
└── fixtures/               # Test data
```

### Example Test
```python
import pytest
from agent import mcp_agent

@pytest.mark.asyncio
async def test_simple_query():
    response = await mcp_agent.process_query("Calculate 2 + 2")
    
    assert response["success"] is True
    assert "calculator_tool" in response["tools_used"]
    assert "4" in response["final_answer"]
```

## 📊 Monitoring

### Health Monitoring
```bash
# Check agent health
curl http://localhost:8000/health

# Monitor tool availability
curl http://localhost:8000/tools
```

### Logging
Logs are structured and include:
- Request/response details  
- Tool execution traces
- Error information with stack traces
- Performance metrics

**Log Location**: `logs/mcp_agent.log`

**Log Format:**
```
2024-12-02 10:30:00 | INFO | Processing query: Calculate 2+2
2024-12-02 10:30:01 | INFO | Selected 1 tools: calculator_tool  
2024-12-02 10:30:01 | INFO | Tool calculator_tool execution completed successfully
2024-12-02 10:30:02 | INFO | Query processed successfully in 1.23s
```

### Performance Metrics
- Query processing time
- Tool execution duration
- Success/failure rates
- Resource usage (CPU, memory)

## 🚀 Deployment

### Docker Deployment
```bash
# Production deployment
docker-compose --profile production up -d

# With custom environment
docker-compose --env-file .env.prod up -d
```

### Cloud Deployment

#### AWS ECS
```bash
# Build and push to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-west-2.amazonaws.com
docker build -t mcp-agent .
docker tag mcp-agent:latest <account>.dkr.ecr.us-west-2.amazonaws.com/mcp-agent:latest
docker push <account>.dkr.ecr.us-west-2.amazonaws.com/mcp-agent:latest
```

#### Google Cloud Run
```bash
# Deploy to Cloud Run
gcloud run deploy mcp-agent \
  --image gcr.io/$PROJECT_ID/mcp-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Environment-Specific Configurations

**Development** (`.env.dev`):
```bash
DEBUG=true
LOG_LEVEL=debug
RELOAD=true
```

**Production** (`.env.prod`):
```bash
DEBUG=false
LOG_LEVEL=info
RELOAD=false
WORKERS=4
```

## 🗺️ Roadmap

### Phase 1: Core Enhancement ✅
- [x] Multi-step tool reasoning
- [x] Comprehensive error handling  
- [x] Docker deployment
- [x] Interactive web UI

### Phase 2: Advanced Features 🚧  
- [ ] Tool output caching
- [ ] Custom tool plugins API
- [ ] Streaming responses
- [ ] Authentication & authorization
- [ ] Rate limiting

### Phase 3: Enterprise Features 📋
- [ ] Multi-agent orchestration
- [ ] Workflow automation
- [ ] Integration marketplace  
- [ ] Advanced analytics dashboard
- [ ] Enterprise SSO

### Phase 4: AI Enhancements 🔮
- [ ] Tool learning from usage patterns
- [ ] Automatic tool creation
- [ ] Advanced reasoning capabilities
- [ ] Multimodal tool support

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/yourusername/mcp-tool-calling-agent.git
cd mcp-tool-calling-agent

# Create a feature branch
git checkout -b feature/amazing-feature

# Make your changes and test
pytest backend/tests/

# Submit a pull request
```

### Contribution Guidelines
1. **Code Quality**: Follow PEP 8, add type hints, write tests
2. **Documentation**: Update README and docstrings  
3. **Testing**: Ensure all tests pass and add new ones
4. **Commit Messages**: Use conventional commits format

### Issues and Feature Requests
- 🐛 **Bug Reports**: Use the bug report template
- ✨ **Feature Requests**: Use the feature request template  
- 🤔 **Questions**: Use GitHub Discussions

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** - For GPT models and API
- **FastAPI** - For the excellent web framework
- **Sentence Transformers** - For embedding models  
- **FAISS** - For vector search capabilities
- **Open-Meteo** - For free weather API

---

## 📞 Support

- **Documentation**: This README and `/docs` endpoint
- **Community**: GitHub Discussions
- **Issues**: GitHub Issues  
- **Email**: [your-email@domain.com]

---

**⭐ If this project helps you, please give it a star on GitHub! ⭐**