# 📚 AutoDocGen - Automatic Technical Documentation Generator

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![LM Studio](https://img.shields.io/badge/LM_Studio-Qwen3_4B-orange.svg)](https://lmstudio.ai/)
[![Ollama](https://img.shields.io/badge/Ollama-Qwen3-orange.svg)](https://ollama.ai/)

A smart web tool that analyzes public GitHub repositories and automatically generates complete technical documentation using local Generative AI (LLM).

## 🎯 About the Project

**AutoDocGen** is a web platform that automates the creation of technical documentation for software projects. Leveraging the power of Generative Artificial Intelligence through LM Studio or Ollama, the tool analyzes GitHub repositories and produces structured documentation including:

- ✅ **Functional and Non-Functional Requirements**
- ✅ **Software Architecture** with Mermaid Diagrams
- ✅ **Mermaid Diagrams (graph TD)**
- ✅ **Technology Stack and Dependencies**
- ✅ **Executive Project Summary**

## 🚀 Features

- 🔐 **Secure authentication** with JWT
- 📦 **Public repository analysis** from GitHub
- 🤖 **Automatic documentation generation** with AI (LLM Models)
- 💬 **Persistent chat** per repository with SQLite history
- 📊 **Interactive dashboard** with analysis history
- 📄 **Export in Markdown and PDF**
- 🎨 **Architectural diagrams** in Mermaid (graph TD with auto-sanitization)
- ⚡ **Asynchronous processing** of analyses (background tasks)
- 💾 **Persistent storage** of results
- 📡 **Real-time monitoring** of analysis stages (interactive terminal in frontend)
- 🔄 **Dual LLM provider** — auto-detects LM Studio (port 1234) or Ollama (port 11434)
- 📝 **Structured logging system** with log file per component (backend and frontend)
- 🩺 **Startup health checks** — database, LLM, dependencies, and directories

## 📋 Prerequisites

Before getting started, make sure you have installed:

- **Python 3.8+**
- **uv** (to manage Python libraries)
- **Git** (to clone the repository)
- **One LLM provider:**
  - **LM Studio** (recommended) with Qwen3-4B-2507 model loaded on port 1234, OR
  - **Ollama** with Qwen3 model on port 11434

### Installing LM Studio (Recommended)

1. Download and install LM Studio from: https://lmstudio.ai
2. Search and download the model `qwen3-4b-2507`
3. Load the model and start the local inference server on port 1234

### Installing Ollama (Alternative)

1. Download and install Ollama from: https://ollama.ai/download
2. Pull the Qwen3 model:
   ```bash
   ollama pull qwen3
   ```
3. Start the server:
   ```bash
   ollama serve
   ```

> ⚠️ The backend auto-detects which provider is running — you don't need to configure anything.

### Troubleshooting xhtml2pdf (Linux)

xhtml2pdf indirectly depends on pycairo (via rlpycairo → svglib), which requires Cairo development libraries:

```bash
sudo apt update
sudo apt install -y \
    libcairo2-dev \
    pkg-config \
    libpango1.0-dev \
    libglib2.0-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    python3-dev
```

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/autodocgen.git
cd autodocgen
```

### 2. Project Structure

```
autodocgen/
├── backend/          # FastAPI API
│   └── logs/         # Structured logs by component (generated at runtime)
├── frontend/         # Flask Interface
│   └── logs/         # Frontend logs (generated at runtime)
├── storage/          # Temporary files and generated documents
├── README.md
└── LICENSE
```

### 3. Installing Dependencies

**Backend (FastAPI):**
```bash
cd backend
uv venv
uv pip install -r requirements.txt
```

**Frontend (Flask):**
```bash
cd ../frontend
uv venv
uv pip install -r requirements.txt
```

## 🏃 Running the Application

You will need **two terminals** open simultaneously.

### Terminal 1: Backend (FastAPI)

```bash
cd backend
uv run uvicorn app.main:app --port 8000
```

✅ The backend will be running at: **http://127.0.0.1:8000**

### Terminal 2: Frontend (Flask)

```bash
cd frontend
uv run app.py
```

✅ The frontend will be running at: **http://127.0.0.1:5001**

## 📖 Using the System

### Step-by-Step Guide

1. **Access the application**
   - Open your browser and go to: http://127.0.0.1:5001

2. **Create your account**
   - Click "Register" in the menu
   - Fill in your details and create an account

3. **Log in**
   - Use your credentials to access the dashboard

4. **Add a repository**
   - On the dashboard, click "Add Repository"
   - Enter the URL of a public GitHub repository
   - Example: `https://github.com/psf/requests`

5. **Start the analysis**
   - Click "Analyze 🚀"
   - The analysis screen will display an **interactive terminal** showing each step of the process in real-time (ZIP download, indexing, LLM call, etc.) via AJAX polling every 2 seconds
   - You can close the page at any time; the analysis continues in the background on the server
   - When you reopen the analysis page, the terminal will reload with all previously executed steps

6. **View and download the documentation**
   - Access the analysis history
   - View the generated documentation in rendered Markdown (with Mermaid diagram support)
   - Expand the **"View analysis execution log"** accordion to review all steps
   - Download in PDF format

7. **Chat with the repository**
   - On the dashboard, click "Chat 💬" next to any repository
   - Ask questions in natural language about the repository's architecture, requirements, or code
   - Sessions are persisted in SQLite — close and reopen the page without losing history

## 🛠️ Technologies Used

### Backend
- **FastAPI** - Modern and fast web framework
- **SQLAlchemy** - ORM for database
- **bcrypt** - Password hashing (native, no passlib)
- **PyJWT / python-jose** - JWT Authentication
- **HTTPX** - Asynchronous HTTP client
- **xhtml2pdf** - PDF generation from HTML/Markdown
- **LLM Provider** - Auto-detects LM Studio or Ollama
- **logging (stdlib)** - Structured logging system with handlers for console and file

### Frontend
- **Flask** - Lightweight web framework
- **Bootstrap 5.2** - Responsive design
- **JavaScript (Fetch API)** - AJAX polling for real-time monitoring
- **marked.js** - Markdown rendering in browser
- **mermaid.js** - Architectural diagram rendering (individual render with fallback)
- **logging (stdlib)** - Structured logging system with handlers for console and file

### Database
- **SQLite** - Relational database (MVP)
- **PostgreSQL** - Recommended for production

### Generative AI
- **LM Studio** (recommended) - Local LLM server with Qwen3-4B-2507
- **Ollama** (alternative) - Local LLM server with Qwen3
- **OpenCode API** (optional) - Pre-computed analysis enrichment, port 7000

## 📁 File Structure

```
backend/
├── app/
│   ├── routers/
│   │   ├── auth.py              # Authentication and registration endpoints
│   │   ├── repos.py             # Repository management endpoints
│   │   ├── analyses.py          # Analysis endpoints + GET /{id}/steps endpoint
│   │   └── chat.py              # Chat endpoints (send, sessions, history, delete)
│   ├── services/
│   │   ├── llm_provider.py      # Auto-detects LM Studio or Ollama
│   │   ├── lm_studio_client.py  # LM Studio API integration (port 1234)
│   │   ├── ollama_client.py     # Ollama API integration (port 11434)
│   │   ├── opencode_client.py   # OpenCode API integration (optional, port 7000)
│   │   ├── chat_service.py      # Chat session management with SQLite persistence
│   │   ├── github_fetcher.py    # GitHub ZIP download
│   │   ├── repo_indexer.py      # File traversal and indexing
│   │   ├── context_builder.py   # Evidence package construction
│   │   ├── doc_generator.py     # Documentation generation orchestration
│   │   └── pdf_generator.py     # Markdown → PDF conversion (xhtml2pdf)
│   ├── logging_config.py        # Dual-channel logger utility (console + file)
│   ├── models.py                # SQLAlchemy models (User, Repository, AnalysisJob, Document, ChatSession, ChatMessage)
│   ├── schemas.py               # Pydantic v2 schemas
│   ├── database.py              # SQLAlchemy configuration and SessionLocal
│   ├── security.py              # Native bcrypt password hashing/verification
│   └── main.py                  # FastAPI app with lifespan and startup checks
├── logs/                        # Log files generated at runtime
│   ├── initialization.log
│   ├── analyses.log
│   ├── repos.log
│   ├── llm_provider.log
│   ├── ollama_client.log
│   ├── github_fetcher.log
│   ├── context_builder.log
│   ├── repo_indexer.log
│   ├── doc_generator.log
│   └── pdf_generator.log
├── storage/
│   ├── repos/                   # Temporarily extracted ZIPs per job
│   └── docs/                    # Generated PDFs
└── requirements.txt
```

```
frontend/
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── analysis_result.html     # Interactive terminal with AJAX polling + Mermaid rendering
│   ├── analyzed_repos.html
│   └── chat.html                # Chat interface with session list
├── static/
│   └── css/
├── logging_config.py            # Dual-channel logger utility (console + file)
├── logs/                        # Log files generated at runtime
│   └── initialization.log
├── app.py                       # Flask app with startup checks and chat route
└── requirements.txt
```

## 🔧 Advanced Configuration

### Environment Variables

Create a `.env` file in the `backend/` folder:

```env
# Database
DATABASE_URL=sqlite:///./storage/app.db

# JWT
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# GitHub
GITHUB_API_TOKEN=your_token_here (optional)

# Limits
MAX_REPO_SIZE_MB=100
MAX_FILE_COUNT=500
ANALYSIS_TIMEOUT_SECONDS=300
```

No LLM configuration is needed — the backend auto-detects LM Studio (port 1234) or Ollama (port 11434) at startup.

### Docker (Optional)

To run with Docker:

Create Dockerfile files for the backend and frontend applications.

```bash
docker-compose up --build
```

## 🐛 Troubleshooting

### LLM provider is not responding
```bash
# Check LM Studio
curl http://localhost:1234/v1/models

# Check Ollama
curl http://localhost:11434/api/version
```

> ⚠️ The backend startup log (`logs/initialization.log`) reports which provider was detected and lists available models.

### Dependency errors
```bash
# Update pip
pip install --upgrade pip

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Corrupted or outdated database schema
```bash
# Remove the database (warning: deletes all data)
rm -f backend/app.db

# The database will be automatically recreated on next backend startup
uv run uvicorn app.main:app --port 8000
```

### Checking startup logs
```bash
# Backend
cat backend/logs/initialization.log

# Frontend
cat frontend/logs/initialization.log
```

### Checking logs for a specific analysis
```bash
# Full analysis pipeline
cat backend/logs/analyses.log

# LLM calls
cat backend/logs/llm_provider.log
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the project
2. Create a branch for your feature (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## 📝 Future Improvements

- [ ] Support for private repositories (GitHub OAuth)
- [ ] Incremental analysis (detect changes)
- [ ] Documentation version comparison
- [ ] CI/CD pipeline integration
- [ ] User administration interface
- [ ] Notification system (email/webhook upon analysis completion)
- [ ] Public API for external integrations
- [ ] Database migration with Alembic (avoid manual `app.db` reset)
- [ ] Server-Sent Events (SSE) to replace AJAX polling with real-time push
- [ ] Docker Compose support with integrated LLM

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

Developed by [Armando Soares Sousa]

## 🙏 Acknowledgments

- LM Studio Team for excellent local LLM tooling
- Ollama Team for their excellent work with local LLMs
- FastAPI and Flask communities
- All contributors and users

## 📞 Support

For support, please open an issue in the repository or contact [armando@ufpi.edu.br].
