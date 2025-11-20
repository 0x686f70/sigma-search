"""
Parallel rule loading for faster startup.
Uses multiprocessing to load rules from multiple directories simultaneously.
"""
import os
import yaml
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def load_rules_from_file(file_path: str, rules_dir: str) -> Dict[str, Any] | None:
    """
    Load a single rule file.
    
    Args:
        file_path: Absolute path to rule file
        rules_dir: Base rules directory for relative path calculation
        
    Returns:
        Rule dictionary or None if invalid
    """
    try:
        # Skip files larger than 1MB
        if os.path.getsize(file_path) > 1024 * 1024:
            return None
        
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            raw_content = f.read()
            
        try:
            data = yaml.safe_load(raw_content)
        except yaml.YAMLError:
            return None
        
        if not data or not isinstance(data, dict):
            return None
        
        # Validate required fields
        if not any(key in data for key in ['title', 'detection']):
            return None
        
        return {
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'tags': data.get('tags', []) if isinstance(data.get('tags'), list) else [],
            'file_path': os.path.relpath(file_path, rules_dir).replace(os.sep, '/'),
            'logsource': data.get('logsource', {}) if isinstance(data.get('logsource'), dict) else {},
            'content': raw_content
        }
    
    except (IOError, OSError):
        return None


def collect_rule_files(search_dirs: List[str]) -> List[str]:
    """
    Collect all rule file paths from search directories.
    
    Args:
        search_dirs: List of directories to search
        
    Returns:
        List of absolute file paths
    """
    rule_files = []
    seen_files = set()
    
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
        
        for root, _, files in os.walk(search_dir):
            for file in files:
                if file.startswith('.') or not (file.endswith('.yml') or file.endswith('.yaml')):
                    continue
                
                file_path = os.path.join(root, file)
                
                # Avoid duplicates
                if file_path in seen_files:
                    continue
                seen_files.add(file_path)
                
                rule_files.append(file_path)
    
    return rule_files


def load_rules_parallel(rules_dir: str, max_workers: int = 4) -> List[Dict[str, Any]]:
    """
    Load rules in parallel using thread pool.
    
    Args:
        rules_dir: Base rules directory
        max_workers: Maximum number of parallel workers
        
    Returns:
        List of loaded rules
    """
    import time
    start_time = time.time()
    
    # Determine search directories
    search_dirs = [rules_dir]
    
    additional_rule_dirs = [
        'rules-emerging-threats',
        'rules-threat-hunting',
        'rules-compliance',
        'rules-dfir',
        'rules-placeholder'
    ]
    
    for dir_name in additional_rule_dirs:
        dir_path = os.path.join(rules_dir, dir_name)
        if os.path.exists(dir_path):
            search_dirs.append(dir_path)
    
    # Collect all rule files
    logger.info(f"Scanning {len(search_dirs)} directories for rules...")
    rule_files = collect_rule_files(search_dirs)
    logger.info(f"Found {len(rule_files)} rule files")
    
    # Load rules in parallel
    rules = []
    loaded_count = 0
    failed_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(load_rules_from_file, file_path, rules_dir): file_path
            for file_path in rule_files
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_file):
            try:
                rule = future.result()
                if rule:
                    rules.append(rule)
                    loaded_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
                logger.debug(f"Failed to load rule: {e}")
    
    elapsed = time.time() - start_time
    logger.info(f"Parallel loading completed: {loaded_count} loaded, {failed_count} skipped in {elapsed:.2f}s")
    
    return rules
