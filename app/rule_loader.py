import os
import yaml
import re

def load_rules(rules_dir):
    """
    Load all Sigma rules from the given directory and its subdirectories.
    
    The loader searches in:
    1. Root directory (sigma_rules/) - contains standard rules copied from 'rules/' folder
    2. rules-emerging-threats/ - emerging threat detection rules
    3. rules-threat-hunting/ - threat hunting rules
    4. rules-compliance/ - compliance rules
    5. rules-dfir/ - DFIR rules
    
    Note: The standard 'rules/' content is copied directly to sigma_rules/ root for backward compatibility.
    """
    rules = []
    
    # Start with root directory (contains standard rules from 'rules/' folder)
    search_dirs = [rules_dir]
    
    # Add rules-* subdirectories if they exist
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
                # Skip files larger than 1MB
                if os.path.getsize(file_path) > 1024 * 1024:
                    continue
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        raw_content = f.read()
                        try:
                            data = yaml.safe_load(raw_content)
                        except yaml.YAMLError:
                            continue
                            
                        if not data or not isinstance(data, dict):
                            continue
                        
                        # Validate required fields
                        if not any(key in data for key in ['title', 'detection']):
                            continue
                            
                        rules.append({
                            'title': data.get('title', ''),
                            'description': data.get('description', ''),
                            'tags': data.get('tags', []) if isinstance(data.get('tags'), list) else [],
                            'file_path': os.path.relpath(file_path, rules_dir).replace(os.sep, '/'),
                            'logsource': data.get('logsource', {}) if isinstance(data.get('logsource'), dict) else {},
                            'content': raw_content
                        })
                except (IOError, OSError) as e:
                    continue
    return rules

def search_rules(rules, query):
    """
    Search rules by query in title, description, tags, or raw YAML content.
    Supports AND/OR conditions, e.g., 'mimikatz AND registry' or 'powershell OR wmi'.
    """
    # Tokenize query for AND/OR logic
    tokens = re.split(r'\s+(AND|OR)\s+', query, flags=re.IGNORECASE)
    terms = []
    ops = []
    for i, token in enumerate(tokens):
        if i % 2 == 0:
            terms.append(token.strip().lower())
        else:
            ops.append(token.strip().upper())

    def rule_matches(rule, term):
        title = rule.get('title', '').lower()
        description = rule.get('description', '').lower()
        tags = [str(tag).lower() for tag in rule.get('tags', [])]
        raw_content = rule.get('content', '').lower()
        return (
            term in title
            or term in description
            or any(term in tag for tag in tags)
            or any(tag.endswith('.' + term) for tag in tags)
            or term in raw_content
        )

    results = []
    for rule in rules:
        match = rule_matches(rule, terms[0])
        for i, op in enumerate(ops):
            if op == 'AND':
                match = match and rule_matches(rule, terms[i + 1])
            elif op == 'OR':
                match = match or rule_matches(rule, terms[i + 1])
        if match:
            results.append(rule)
    return results
