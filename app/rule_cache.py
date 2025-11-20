"""
Rule caching system for faster application startup.
Caches parsed rules to disk to avoid re-parsing on every startup.
"""
import os
import pickle
import hashlib
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.cache')
CACHE_FILE = os.path.join(CACHE_DIR, 'rules_cache.pkl')
CACHE_HASH_FILE = os.path.join(CACHE_DIR, 'rules_hash.txt')


def get_directory_hash(rules_dir: str) -> str:
    """
    Calculate hash of rules directory to detect changes.
    Uses modification times and file count for speed.
    """
    try:
        hash_data = []
        
        # Walk through all rule directories
        for root, dirs, files in os.walk(rules_dir):
            # Skip hidden directories and cache
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.endswith(('.yml', '.yaml')):
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        # Use file path, size, and mtime for hash
                        hash_data.append(f"{file_path}:{stat.st_size}:{stat.st_mtime}")
                    except OSError:
                        continue
        
        # Create hash from all file info
        hash_string = '|'.join(sorted(hash_data))
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    except Exception as e:
        logger.warning(f"Failed to calculate directory hash: {e}")
        return ""


def save_cache(rules: List[Dict[str, Any]], rules_dir: str) -> bool:
    """
    Save parsed rules to cache file.
    
    Args:
        rules: List of parsed rule dictionaries
        rules_dir: Path to rules directory
        
    Returns:
        True if cache saved successfully
    """
    try:
        # Ensure cache directory exists
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        # Calculate directory hash
        dir_hash = get_directory_hash(rules_dir)
        
        # Save rules to pickle file
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(rules, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        # Save hash
        with open(CACHE_HASH_FILE, 'w') as f:
            f.write(dir_hash)
        
        logger.info(f"Cached {len(rules)} rules to disk")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save cache: {e}")
        return False


def load_cache(rules_dir: str) -> List[Dict[str, Any]] | None:
    """
    Load rules from cache if valid.
    
    Args:
        rules_dir: Path to rules directory
        
    Returns:
        List of cached rules or None if cache invalid/missing
    """
    try:
        # Check if cache files exist
        if not os.path.exists(CACHE_FILE) or not os.path.exists(CACHE_HASH_FILE):
            logger.info("No cache found")
            return None
        
        # Read stored hash
        with open(CACHE_HASH_FILE, 'r') as f:
            stored_hash = f.read().strip()
        
        # Calculate current hash
        current_hash = get_directory_hash(rules_dir)
        
        # Check if hash matches
        if stored_hash != current_hash:
            logger.info("Cache invalidated (rules directory changed)")
            return None
        
        # Load cached rules
        with open(CACHE_FILE, 'rb') as f:
            rules = pickle.load(f)
        
        logger.info(f"Loaded {len(rules)} rules from cache")
        return rules
        
    except Exception as e:
        logger.warning(f"Failed to load cache: {e}")
        return None


def clear_cache() -> bool:
    """
    Clear the rules cache.
    
    Returns:
        True if cache cleared successfully
    """
    try:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        if os.path.exists(CACHE_HASH_FILE):
            os.remove(CACHE_HASH_FILE)
        logger.info("Cache cleared")
        return True
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        return False
