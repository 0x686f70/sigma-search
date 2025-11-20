import logging
import os
import yaml
from .config import ensure_rules_dir, ensure_custom_rules_dir
from .rule_loader import load_rules
from .rule_cache import load_cache, save_cache
from .parallel_loader import load_rules_parallel

# Global rules list
rules = []

# Flag to track if we should use optimized loading
USE_OPTIMIZED_LOADING = os.environ.get('SIGMA_OPTIMIZED_LOADING', 'True').lower() == 'true'

def load_sigma_rules():
    """Load Sigma rules from the rules directory, including custom rules and emerging threats."""
    import time
    try:
        start_time = time.time()
        rules_dir_abs = ensure_rules_dir()
        
        # Ensure custom rules directory exists (but don't load separately)
        ensure_custom_rules_dir()
        
        loaded_rules = None
        
        # Try optimized loading if enabled
        if USE_OPTIMIZED_LOADING:
            # Try to load from cache first
            load_start = time.time()
            loaded_rules = load_cache(rules_dir_abs)
            
            if loaded_rules:
                logging.info(f"  -> Loaded {len(loaded_rules)} rules from cache in {time.time() - load_start:.2f}s")
            else:
                # Cache miss - use parallel loading
                load_start = time.time()
                loaded_rules = load_rules_parallel(rules_dir_abs, max_workers=4)
                logging.info(f"  -> Parallel loaded {len(loaded_rules)} rules in {time.time() - load_start:.2f}s")
                
                # Save to cache for next time
                save_cache(loaded_rules, rules_dir_abs)
        
        # Fallback to traditional loading if optimized loading disabled or failed
        if not loaded_rules:
            load_start = time.time()
            loaded_rules = load_rules(rules_dir_abs)
            logging.info(f"  -> Traditional loaded {len(loaded_rules)} rules in {time.time() - load_start:.2f}s")
        
        rules.clear()
        rules.extend(loaded_rules)
        
        # Count rules by source directory
        custom_count = len([r for r in loaded_rules if r['file_path'].startswith('customs/')])
        emerging_threats_count = len([r for r in loaded_rules if r['file_path'].startswith('rules-emerging-threats/')])
        threat_hunting_count = len([r for r in loaded_rules if r['file_path'].startswith('rules-threat-hunting/')])
        compliance_count = len([r for r in loaded_rules if r['file_path'].startswith('rules-compliance/')])
        dfir_count = len([r for r in loaded_rules if r['file_path'].startswith('rules-dfir/')])
        placeholder_count = len([r for r in loaded_rules if r['file_path'].startswith('rules-placeholder/')])
        
        # Standard rules are in root directories (windows/, linux/, cloud/, etc.)
        # They don't start with 'rules-' or 'customs/'
        special_dirs = ['customs/', 'rules-emerging-threats/', 'rules-threat-hunting/', 
                       'rules-compliance/', 'rules-dfir/', 'rules-placeholder/']
        standard_rules_count = len([r for r in loaded_rules 
                                   if not any(r['file_path'].startswith(d) for d in special_dirs)])
        
        other_count = 0  # All rules should be categorized now
        
        # Build detailed log message
        log_parts = []
        if standard_rules_count > 0:
            log_parts.append(f"{standard_rules_count} standard")
        if emerging_threats_count > 0:
            log_parts.append(f"{emerging_threats_count} emerging-threats")
        if threat_hunting_count > 0:
            log_parts.append(f"{threat_hunting_count} threat-hunting")
        if compliance_count > 0:
            log_parts.append(f"{compliance_count} compliance")
        if dfir_count > 0:
            log_parts.append(f"{dfir_count} dfir")
        if placeholder_count > 0:
            log_parts.append(f"{placeholder_count} placeholder")
        if custom_count > 0:
            log_parts.append(f"{custom_count} custom")
        if other_count > 0:
            log_parts.append(f"{other_count} other")
        
        log_message = f"Loaded {len(loaded_rules)} total Sigma rules"
        if log_parts:
            log_message += f" ({', '.join(log_parts)})"
        
        logging.info(log_message)
        return rules
    except Exception as e:
        logging.error(f"Failed to load rules: {str(e)}")
        return []

def get_rules():
    """Get the current rules list."""
    return rules 