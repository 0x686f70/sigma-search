import re

def format_subcategory(subcategory):
    """Format subcategory name to be more readable."""
    return ' '.join(word.capitalize() for word in subcategory.replace('_', ' ').split())

def extract_subcategory(file_path, category):
    """Extract subcategory from file path based on the main category."""
    parts = file_path.lower().split('/')
    try:
        cat_index = parts.index(category.lower())
        if cat_index + 1 < len(parts):
            return format_subcategory(parts[cat_index + 1])
    except ValueError:
        pass
    return 'Other'

def group_and_sort_rules(rules, category=None):
    """
    Group rules by subcategory when a category is selected, otherwise by product/category.
    Args:
        rules: List of rule dictionaries
        category: Optional category filter being applied
    """
    # Special categories that should be grouped by logsource
    special_categories = ['customs', 'rules-emerging-threats', 'rules-threat-hunting', 
                         'rules-compliance', 'rules-dfir']
    
    if category and category.lower() in special_categories:
        # Special handling for these categories - group by logsource product
        grouped = {}
        for rule in rules:
            group_key = 'Unknown'
            if 'logsource' in rule and isinstance(rule['logsource'], dict):
                prod = rule['logsource'].get('product', '').strip()
                if prod:
                    group_key = prod.capitalize()
                else:
                    cat = rule['logsource'].get('category', '').strip()
                    if cat:
                        group_key = cat.capitalize()
            
            if group_key not in grouped:
                grouped[group_key] = []
            grouped[group_key].append(rule)
        
        # Sort groups and rules within each group
        sorted_groups = {}
        for group_key in sorted(grouped.keys()):
            sorted_groups[group_key] = sorted(
                grouped[group_key],
                key=lambda r: (r.get('title') or r.get('file_path', '')).lower()
            )
        return sorted_groups
    
    elif category:
        # When a non-customs category is selected, group by subcategory
        grouped = {}
        for rule in rules:
            subcategory = extract_subcategory(rule['file_path'], category)
            if subcategory not in grouped:
                grouped[subcategory] = []
            grouped[subcategory].append(rule)
        
        # Sort subcategories alphabetically
        sorted_groups = {}
        for subcategory in sorted(grouped.keys()):
            # Sort rules within each subcategory by title or filepath
            sorted_groups[subcategory] = sorted(
                grouped[subcategory],
                key=lambda r: (r.get('title') or r.get('file_path', '')).lower()
            )
        return sorted_groups
    
    # If no category filter, use original grouping logic
    product_set = set()
    for rule in rules:
        group_key = 'Unknown'
        if 'logsource' in rule and isinstance(rule['logsource'], dict):
            prod = rule['logsource'].get('product', '').strip()
            if prod:
                group_key = prod.capitalize()
            else:
                cat = rule['logsource'].get('category', '').strip()
                if cat:
                    group_key = cat.capitalize()
        product_set.add(group_key)
        
    priority_products = ['Windows', 'Linux', 'Antivirus']
    product_list = [p for p in priority_products if p in product_set]
    others = sorted([p for p in product_set if p not in priority_products and p != 'Unknown'])
    
    if 'Unknown' in product_set:
        product_list += others + ['Unknown']
    else:
        product_list += others
        
    grouped = {p: [] for p in product_list}
    for rule in rules:
        group_key = 'Unknown'
        if 'logsource' in rule and isinstance(rule['logsource'], dict):
            prod = rule['logsource'].get('product', '').strip()
            if prod:
                group_key = prod.capitalize()
            else:
                cat = rule['logsource'].get('category', '').strip()
                if cat:
                    group_key = cat.capitalize()
        grouped[group_key].append(rule)
        
    for p in grouped:
        grouped[p].sort(key=lambda r: (r.get('title') or r.get('file_path', '')).lower())
    
    return grouped
