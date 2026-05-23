from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
import httpx
import os
from .database import engine, Base, SessionLocal
from .routers import auth, repos, analyses, chat
from .logging_config import get_custom_logger

logger = get_custom_logger("initialization", "initialization.log")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Verification ---
    logger.info("==========================================")
    logger.info("Initializing Github Repo Analyzer Backend...")
    
    # 1. Database Check
    logger.info("Checking database connection...")
    try:
        # Create Tables first to ensure database schema is up-to-date
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Database Connection verified successfully.")
    except Exception as e:
        logger.error(f"Database Connection failed: {e}")
        
    # 2. LLM Provider Check
    logger.info("Checking LLM providers (LM Studio / Ollama)...")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            # LM Studio
            try:
                resp = await client.get("http://localhost:1234/v1/models")
                if resp.status_code == 200:
                    models = [m["id"] for m in resp.json().get("data", [])]
                    logger.info(f"LM Studio detected on port 1234. Models: {models}")
                else:
                    logger.warning(f"LM Studio responded with status {resp.status_code}")
            except Exception:
                logger.warning("LM Studio not detected on port 1234")

            # Ollama
            try:
                resp = await client.get("http://localhost:11434/api/tags")
                if resp.status_code == 200:
                    models = [m["name"] for m in resp.json().get("models", [])]
                    logger.info(f"Ollama detected on port 11434. Models: {models}")
                else:
                    logger.warning(f"Ollama responded with status {resp.status_code}")
            except Exception:
                logger.warning("Ollama not detected on port 11434")
    except Exception as e:
        logger.error(f"Error during LLM provider check: {e}")
        
    # 3. Dependency Imports Check
    logger.info("Checking critical packages dependencies...")
    dependencies = [
        ("bcrypt", "bcrypt"),
        ("jose", "python-jose"),
        ("xhtml2pdf", "xhtml2pdf"),
        ("sqlalchemy", "sqlalchemy"),
        ("fastapi", "fastapi")
    ]
    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
            logger.info(f"Dependency '{package_name}' is verified.")
        except ImportError as e:
            logger.error(f"Dependency '{package_name}' import failed: {e}")
            
    # 4. Storage Directories Check
    logger.info("Checking storage directories...")
    for directory in ["storage/repos", "storage/docs"]:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Directory '{directory}' verified.")
        
    logger.info("Backend Application initialization process completed.")
    logger.info("==========================================")
    
    yield
    
    logger.info("Shutting down Github Repo Analyzer Backend...")

app = FastAPI(title="Github Repo Analyzer", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5001", "http://127.0.0.1:5001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(repos.router)
app.include_router(analyses.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"message": "API is running"}
