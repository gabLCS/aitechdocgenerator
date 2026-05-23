import os
from ..logging_config import get_custom_logger

logger = get_custom_logger("repo_indexer", "repo_indexer.log")

# Directories to ignore
IGNORE_DIRS = {
    ".git", ".github", ".vscode", ".idea", 
    "node_modules", "dist", "build", "coverage", 
    "__pycache__", ".venv", "venv", "env"
}

# Key files to look for
KEY_FILES = {
    "README.md", "pyproject.toml", "requirements.txt", 
    "package.json", "Dockerfile", "docker-compose.yml",
    "pom.xml", "build.gradle", "go.mod", "Cargo.toml",
    "Makefile", "CMakeLists.txt"
}

def index_repo(repo_path: str):
    """
    Walks the repo to generate a file tree and find key files.
    """
    logger.info(f"Starting directory traversal/indexing for: '{repo_path}'")
    file_tree = []
    key_files_found = []
    stats = {"files": 0, "extensions": {}}
    
    # We want relative paths for the tree
    base_len = len(repo_path) + 1 

    for root, dirs, files in os.walk(repo_path):
        # Modify dirs in-place to skip ignored ones
        original_dirs = list(dirs)
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        ignored = set(original_dirs) - set(dirs)
        if ignored:
            logger.info(f"Ignoring directories: {list(ignored)} in '{root[base_len:]}'")
        
        for file in files:
            # Skip hidden files or lock files if desired, but some are useful
            if file.startswith(".DS_Store"): continue
            
            full_path = os.path.join(root, file)
            rel_path = full_path[base_len:]
            
            file_tree.append(rel_path)
            stats["files"] += 1
            
            ext = os.path.splitext(file)[1]
            stats["extensions"][ext] = stats["extensions"].get(ext, 0) + 1
            
            if file in KEY_FILES or file.lower() == "readme.md":
                key_files_found.append(rel_path)
                logger.info(f"Detected key repository file: '{rel_path}'")
                
    # Sort tree for better display
    file_tree.sort()
    logger.info(f"Indexing completed. Total files found: {stats['files']} | Key files: {len(key_files_found)}")
    
    return {
        "tree": file_tree,
        "key_files": key_files_found,
        "stats": stats,
        "root_path": repo_path
    }

def read_file_content(full_path: str, limit_lines=100):
    """Reads file content with a line limit to avoid huge files."""
    logger.info(f"Reading file content: '{full_path}' | Limit: {limit_lines} lines")
    content = []
    try:
        with open(full_path, "r", errors="ignore") as f:
            for i, line in enumerate(f):
                if i >= limit_lines:
                    content.append(f"\n... (truncated after {limit_lines} lines)")
                    break
                content.append(line)
        file_size_chars = sum(len(line) for line in content)
        logger.info(f"Successfully read file '{full_path}'. Size: {file_size_chars} chars.")
        return "".join(content)
    except Exception as e:
        logger.error(f"Error reading file '{full_path}': {e}")
        return "[Error reading file]"
