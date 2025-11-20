import os
import shutil
import subprocess
import stat
import tempfile
import time
import logging

logger = logging.getLogger(__name__)


def on_rm_error(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def update_sigma_database(rules_dir):
    """
    Update Sigma rules database by cloning from official repository.
    Downloads multiple rule directories: rules, rules-emerging-threats, etc.
    """
    total_start = time.time()
    repo_url = 'https://github.com/SigmaHQ/sigma.git'
    
    # Directories to download from Sigma repository
    rule_directories = [
        'rules',
        'rules-emerging-threats',
        'rules-threat-hunting',
        'rules-compliance',
        'rules-dfir'
    ]
    
    logger.info("Starting Sigma rules update...")
    logger.info(f"Target directories: {', '.join(rule_directories)}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Clone with sparse checkout for faster download
            step_start = time.time()
            logger.info("Cloning Sigma repository (sparse checkout)...")
            subprocess.run(
                ['git', 'clone', '--depth', '1', '--filter=blob:none', '--sparse', repo_url, temp_dir], 
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"  -> Repository cloned in {time.time() - step_start:.2f}s")
            
            # Set sparse-checkout to include multiple directories
            step_start = time.time()
            logger.info(f"Checking out {len(rule_directories)} rule directories...")
            subprocess.run(
                ['git', '-C', temp_dir, 'sparse-checkout', 'set'] + rule_directories, 
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"  -> Directories checked out in {time.time() - step_start:.2f}s")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git operation failed: {e.stderr if hasattr(e, 'stderr') else str(e)}")
            raise RuntimeError(f"Git clone or sparse-checkout failed: {e}")

        # Preserve user custom rules directory and remove old rule directories
        step_start = time.time()
        logger.info("Cleaning old rules...")
        removed_count = 0
        for filename in os.listdir(rules_dir):
            if filename == 'customs':
                continue
            file_path = os.path.join(rules_dir, filename)
            if os.path.isdir(file_path):
                shutil.rmtree(file_path, onerror=on_rm_error)
                removed_count += 1
            elif os.path.isfile(file_path):
                os.remove(file_path)
                removed_count += 1
        logger.info(f"  -> Removed {removed_count} old items in {time.time() - step_start:.2f}s")

        # Copy each rule directory from temp to rules_dir
        step_start = time.time()
        logger.info("Copying new rules...")
        copied_dirs = []
        for dir_name in rule_directories:
            src_path = os.path.join(temp_dir, dir_name)
            if os.path.exists(src_path):
                dir_start = time.time()
                # For 'rules' directory, copy contents directly to maintain backward compatibility
                if dir_name == 'rules':
                    item_count = 0
                    for item in os.listdir(src_path):
                        s = os.path.join(src_path, item)
                        d = os.path.join(rules_dir, item)
                        if os.path.isdir(s):
                            shutil.copytree(s, d)
                        else:
                            shutil.copy2(s, d)
                        item_count += 1
                    logger.info(f"  -> Copied {item_count} items from '{dir_name}' in {time.time() - dir_start:.2f}s")
                else:
                    # For other directories (rules-emerging-threats, etc.), keep directory structure
                    dst_path = os.path.join(rules_dir, dir_name)
                    shutil.copytree(src_path, dst_path)
                    # Count files
                    file_count = sum(1 for root, _, files in os.walk(dst_path) 
                                   for f in files if f.endswith(('.yml', '.yaml')))
                    logger.info(f"  -> Copied '{dir_name}' ({file_count} rules) in {time.time() - dir_start:.2f}s")
                copied_dirs.append(dir_name)
        
        logger.info(f"Total copy time: {time.time() - step_start:.2f}s")
        
        # Clear cache after update
        try:
            from .rule_cache import clear_cache
            clear_cache()
            logger.info("Cache cleared after update")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")
        
        total_time = time.time() - total_start
        logger.info(f"[DONE] Sigma rules update completed in {total_time:.2f}s")
        logger.info(f"Updated directories: {', '.join(copied_dirs)}")
