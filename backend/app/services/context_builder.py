import os
import json
from .repo_indexer import index_repo, read_file_content
from ..logging_config import get_custom_logger

logger = get_custom_logger("context_builder", "context_builder.log")

def build_context(repo_path: str):
    """
    Aggregates repo structure, key file contents, and statistics into a single JSON object.
    This JSON will be the 'Evidence Package' for the LLM.
    """
    logger.info(f"Starting build_context aggregation for repository path: '{repo_path}'")
    
    index_data = index_repo(repo_path)
    logger.info(f"Repository successfully indexed. Tree size: {len(index_data['tree'])} files. Extension stats: {index_data['stats'].get('extensions', {})}")
    
    evidence = {
        "structure": index_data["tree"][:300], # Limit tree size
        "stats": index_data["stats"],
        "files_content": {}
    }
    
    # Read content of key files
    # Prioritize README, then manifests, then maybe source code entry points
    prioritized_files = list(index_data["key_files"])
    
    # Also look for 'main.py' or 'index.js' if not in key files
    common_entry_points = ["main.py", "app.py", "index.js", "server.js", "manage.py"]
    for f in index_data["tree"]:
        if os.path.basename(f) in common_entry_points:
            prioritized_files.append(f)
            
    # Remove duplicates
    prioritized_files = list(set(prioritized_files))
    logger.info(f"Prioritized key files to load content (up to 10): {prioritized_files[:10]}")
    
    for rel_path in prioritized_files[:10]: # Limit to top 10 key files to save context
        full_path = os.path.join(repo_path, rel_path)
        logger.info(f"Reading content of prioritized file: '{rel_path}'")
        evidence["files_content"][rel_path] = read_file_content(full_path)
        
    logger.info(f"Evidence context building completed. Aggregated data: structure={len(evidence['structure'])} files, files_content={len(evidence['files_content'])} files.")
    return evidence
