from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database
from .auth import get_current_user
from ..logging_config import get_custom_logger

logger = get_custom_logger("repos", "repos.log")

router = APIRouter(prefix="/repos", tags=["repos"])

@router.post("/", response_model=schemas.RepositoryResponse)
def create_repository(repo: schemas.RepositoryCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    logger.info(f"User '{current_user.email}' requested repository creation. URL input: '{repo.url}'")
    
    # Basic validation (assume it's a valid github url for MVP)
    # Extract name from URL (simple logic)
    # expected format: https://github.com/owner/repo or just owner/repo
    url = repo.url.strip()
    if "github.com/" in url:
        parts = url.split("github.com/")[-1].split("/")
    else:
        parts = url.split("/")
    
    if len(parts) < 2:
        logger.warning(f"Repository URL parsing failed for input: '{repo.url}'")
        raise HTTPException(status_code=400, detail="Invalid GitHub URL or identifiers")
    
    full_name = f"{parts[0]}/{parts[1]}".replace(".git", "")
    logger.info(f"Repository URL successfully parsed to full_name: '{full_name}'")
    
    new_repo = models.Repository(
        user_id=current_user.id,
        full_name=full_name,
        url=f"https://github.com/{full_name}"
    )
    db.add(new_repo)
    db.commit()
    db.refresh(new_repo)
    logger.info(f"Repository '{full_name}' added successfully. Database ID assigned: {new_repo.id}")
    return new_repo

@router.get("/", response_model=List[schemas.RepositoryResponse])
def read_repositories(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    logger.info(f"User '{current_user.email}' requested repositories list (skip: {skip}, limit: {limit})")
    repos = db.query(models.Repository).filter(models.Repository.user_id == current_user.id).offset(skip).limit(limit).all()
    logger.info(f"Successfully retrieved {len(repos)} repositories for user '{current_user.email}'")
    return repos


@router.get("/{id}", response_model=schemas.RepositoryResponse)
def read_repository(id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    logger.info(f"User '{current_user.email}' requested repository ID: {id}")
    repo = db.query(models.Repository).filter(models.Repository.id == id, models.Repository.user_id == current_user.id).first()
    if not repo:
        logger.warning(f"Repository ID {id} not found or not owned by user '{current_user.email}'")
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo

@router.delete("/{id}")
def delete_repository(id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    logger.info(f"User '{current_user.email}' requested deletion of repository ID: {id}")
    repo = db.query(models.Repository).filter(models.Repository.id == id, models.Repository.user_id == current_user.id).first()
    if not repo:
        logger.warning(f"Repository ID {id} not found or not owned by user '{current_user.email}'")
        raise HTTPException(status_code=404, detail="Repository not found")
    
    repo_name = repo.full_name
    db.delete(repo)
    db.commit()
    logger.info(f"Repository '{repo_name}' (ID {id}) deleted successfully.")
    return {"ok": True}
