import httpx
import shutil
import os
import zipfile
from fastapi import HTTPException
from ..logging_config import get_custom_logger

logger = get_custom_logger("github_fetcher", "github_fetcher.log")

# In a real app, this should be configurable
STORAGE_DIR = "storage/repos"

async def fetch_repo_zip(repo_url: str, job_id: str):
    """
    Downloads the repository ZIP from GitHub and extracts it.
    Assumes repo_url is https://github.com/owner/repo or similar.
    """
    logger.info(f"Initiating fetch_repo_zip for repository URL: '{repo_url}' | Job ID: {job_id}")
    
    if "github.com" not in repo_url:
        logger.warning(f"Failed URL check: '{repo_url}' is not a GitHub repository URL.")
        raise HTTPException(status_code=400, detail="Only GitHub repos are supported")

    # Construct the ZIP URL
    zip_url = f"{repo_url}/archive/HEAD.zip"
    target_dir = os.path.join(STORAGE_DIR, str(job_id))
    os.makedirs(target_dir, exist_ok=True)
    
    zip_path = os.path.join(target_dir, "repo.zip")
    logger.info(f"Downloading repository ZIP from: '{zip_url}' to path: '{zip_path}'")
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            resp = await client.get(zip_url)
            resp.raise_for_status()
            with open(zip_path, "wb") as f:
                f.write(resp.content)
            logger.info(f"Repository ZIP successfully downloaded. Received: {len(resp.content)} bytes.")
        except Exception as e:
            logger.error(f"Failed to download repository ZIP from '{zip_url}': {e}")
            raise HTTPException(status_code=500, detail=f"Failed to download repo: {str(e)}")

    # Extract ZIP
    try:
        logger.info(f"Extracting ZIP archive at '{zip_path}'...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        logger.info(f"Repository ZIP successfully extracted to '{target_dir}'.")
            
        # Cleanup ZIP file
        os.remove(zip_path)
        logger.info(f"Cleaned up ZIP file at '{zip_path}'.")
        
        # Find the root extracted folder
        extracted_folders = [f for f in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, f))]
        if len(extracted_folders) == 1:
            repo_root = os.path.join(target_dir, extracted_folders[0])
            logger.info(f"Found unique repository root folder: '{repo_root}'")
            return repo_root
        else:
            logger.warning(f"Multiple or zero root directories found in extraction. Falling back to: '{target_dir}'")
            return target_dir # Fallback if structure is weird (e.g. flat)
            
    except zipfile.BadZipFile as e:
        logger.error(f"Bad ZIP file downloaded at '{zip_path}': {e}")
        raise HTTPException(status_code=500, detail="Invalid ZIP file downloaded")
