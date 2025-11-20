#!/usr/bin/env python3
"""
Script to check for missing or invalid rule files
"""

import os
from app.rules_manager import load_sigma_rules, get_rules
from app.config import RULES_DIR

def check_rules():
    """Check all rules in the database for file existence"""
    print("Loading rules...")
    load_sigma_rules()
    rules = get_rules()
    
    print(f"Total rules loaded: {len(rules)}")
    print(f"Rules directory: {RULES_DIR}")
    print("\nChecking for missing files...")
    
    missing_files = []
    valid_files = 0
    
    for i, rule in enumerate(rules):
        file_path = rule.get('file_path', '')
        if not file_path:
            print(f"Rule {i}: No file_path")
            continue
            
        abs_path = os.path.join(RULES_DIR, file_path)
        if os.path.exists(abs_path):
            valid_files += 1
        else:
            missing_files.append({
                'index': i,
                'file_path': file_path,
                'title': rule.get('title', 'N/A'),
                'abs_path': abs_path
            })
    
    print(f"\nValid files: {valid_files}")
    print(f"Missing files: {len(missing_files)}")
    
    if missing_files:
        print("\nMissing files:")
        for missing in missing_files[:10]:  # Show first 10
            print(f"  {missing['index']}: {missing['file_path']} - {missing['title']}")
        if len(missing_files) > 10:
            print(f"  ... and {len(missing_files) - 10} more")
    
    return missing_files

if __name__ == "__main__":
    check_rules() 