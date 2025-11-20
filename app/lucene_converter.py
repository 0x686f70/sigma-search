import yaml
import logging
from flask import Response
from .field_mappings import SIGMA_TO_STELLAR_FIELDS, SIGMA_OP_MAP

# Configure logging
logger = logging.getLogger(__name__)


def double_backslashes(value):
    """Double backslashes in string values for Lucene compatibility."""
    if isinstance(value, str):
        # Double all backslashes: \ becomes \\, \\ becomes \\\\
        return value.replace('\\', '\\\\')
    return value


def handle_value_list(field, operator, values):
    """Handle list of values for Lucene query construction."""
    if not values:  # Handle empty list
        return None
        
    sub_clauses = []
    for val in values:
        if isinstance(val, (str, int, float, bool)):
            processed_val = double_backslashes(val)
            str_val = f'"{str(processed_val)}"' if isinstance(val, str) else str(processed_val)
            if operator == "startswith":
                sub_clauses.append(f'{field}:"{str_val}*"')
            elif operator == "endswith":
                sub_clauses.append(f'{field}:"*{str_val}"')
            else:
                sub_clauses.append(f'{field} {operator} {str_val}')
                
    if sub_clauses:
        result = f"({' OR '.join(sub_clauses)})"
        return result
        
    return None


def handle_single_value(field, operator, value):
    """Handle single value for Lucene query construction."""
    if isinstance(value, (str, int, float, bool)):
        processed_val = double_backslashes(value)
        str_val = f'"{str(processed_val)}"' if isinstance(value, str) else str(processed_val)
        return f'{field} {operator} {str_val}'
    return None


def process_detection_section(detection):
    """Process the detection section and extract all field expressions with proper grouping."""
    try:
        selection_groups = {}
        filter_groups = {}
        
        for key, value in detection.items():
            if key in ["condition", "timeframe"]:
                continue
                
            # Handle filter section separately
            if key == "filter":
                if isinstance(value, dict):
                    filter_clauses = []
                    for field_expr, match_values in value.items():
                        clause = process_field_expression(field_expr, match_values)
                        if clause:
                            filter_clauses.append(clause)
                    if filter_clauses:
                        filter_groups[key] = filter_clauses
                continue
                
            if isinstance(value, dict):
                group_clauses = []
                for field_expr, match_values in value.items():
                    clause = process_field_expression(field_expr, match_values)
                    if clause:
                        group_clauses.append(clause)
                if group_clauses:
                    # IMPORTANT: Within each selection group, use AND logic
                    selection_groups[key] = group_clauses
                    
            elif isinstance(value, list):
                list_item_clauses = []
                for idx, item in enumerate(value):
                    if isinstance(item, dict):
                        item_sub_clauses = []
                        for field_expr, match_values in item.items():
                            clause = process_field_expression(field_expr, match_values)
                            if clause:
                                item_sub_clauses.append(clause)
                        if item_sub_clauses:
                            # Within list items, use AND logic
                            combined_item = item_sub_clauses[0] if len(item_sub_clauses) == 1 else f"({' AND '.join(item_sub_clauses)})"
                            list_item_clauses.append(combined_item)
                if list_item_clauses:
                    # Between list items, use OR logic
                    combined_list = list_item_clauses[0] if len(list_item_clauses) == 1 else f"({' OR '.join(list_item_clauses)})"
                    selection_groups[key] = [combined_list]
                    
            elif isinstance(value, str):
                # Handle potential YAML syntax error (missing colon)
                if '|' in value and ('-' in value or value.strip().endswith('|contains') or value.strip().endswith('|startswith') or value.strip().endswith('|endswith')):
                    logger.error(f"YAML syntax error in '{key}': missing colon after field expression. "
                               f"Expected format: 'FieldName|operator:' not 'FieldName|operator'")
                    logger.error(f"Current value: {value}")
                    logger.error(f"Suggested fix: Add ':' after the field expression")
                    # Return empty to show clear error message
                    return {}
                else:
                    logger.warning(f"Unexpected string value in detection section for '{key}': {value}")
            else:
                logger.warning(f"Unexpected value type for '{key}': {type(value)} - {value}")
                    
        # Combine selection and filter groups
        all_groups = {**selection_groups, **filter_groups}
        return all_groups
        
    except Exception as e:
        logger.error(f"Error in process_detection_section: {str(e)}")
        return {}


def process_field_expression(field_expr, match_values):
    """Process a single field expression and its match values."""
    try:
        
        # Handle aggregation functions first
        if '|' in field_expr and 'count()' in field_expr:
            # Handle count() aggregation: selection|count() by field_list comparator number
            return process_count_aggregation(field_expr, match_values)
        elif '|' in field_expr and 'near' in field_expr:
            # Handle near aggregation: selection|near selection
            return process_near_aggregation(field_expr, match_values)
        
        if '|' in field_expr:
            field_parts = field_expr.split('|')
            field_name = field_parts[0]
            ops = [op.strip().lower() for op in field_parts[1:]]
        else:
            field_name = field_expr
            ops = ['is']
            
        stellar_field = SIGMA_TO_STELLAR_FIELDS.get(field_name.strip(), field_name.strip())
        
        # Handle contains|all operator
        if 'all' in ops:
            if isinstance(match_values, list):
                # For contains|all, all values must match (AND condition)
                clauses = []
                for val in match_values:
                    if isinstance(val, (str, int, float, bool)):
                        processed_val = double_backslashes(val)
                        str_val = f'"{str(processed_val)}"' if isinstance(val, str) else str(processed_val)
                        clauses.append(f'{stellar_field} contains {str_val}')
                if clauses:
                    result = f"({' AND '.join(clauses)})"
                    return result
            return None
            
        # Handle regular operators
        operator = SIGMA_OP_MAP.get(ops[0], 'contains')
        
        if isinstance(match_values, list):
            clause = handle_value_list(stellar_field, operator, match_values)
            if clause:
                return clause
        else:
            clause = handle_single_value(stellar_field, operator, match_values)
            if clause:
                return clause
    except Exception as e:
        logger.error(f"Error in process_field_expression: Failed to process '{field_expr}'. Error: {str(e)}")
        return None
    return None


def process_count_aggregation(field_expr, match_values):
    """Process count() aggregation function."""
    try:
        # Format: selection|count() by field_list comparator number
        # For now, return a placeholder since Lucene doesn't directly support count aggregation
        return f"# Count aggregation: {field_expr} - {match_values}"
    except Exception as e:
        logger.error(f"Error in process_count_aggregation: {str(e)}")
        return None


def process_near_aggregation(field_expr, match_values):
    """Process near aggregation function."""
    try:
        # Format: selection|near selection
        # For now, return a placeholder since Lucene doesn't directly support near aggregation
        return f"# Near aggregation: {field_expr} - {match_values}"
    except Exception as e:
        logger.error(f"Error in process_near_aggregation: {str(e)}")
    return None


def _collect_groups_by_pattern(selection_groups, pattern_prefix):
    """Collect selection group expressions for keys matching wildcard pattern like 'selection_*'."""
    try:
        collected = []
        
        # Handle special cases: "them" refers to all selection groups
        if pattern_prefix == "them":
            for key, clauses in selection_groups.items():
                if key != "filter":  # Exclude filter from "them" pattern
                    if len(clauses) == 1:
                        collected.append(clauses[0])
                    else:
                        # IMPORTANT: Within each selection group, use AND logic
                        # This is the key fix - selection groups should use AND between fields
                        collected.append(f"({' AND '.join(clauses)})")
            return collected
        
        for key, clauses in selection_groups.items():
            matches = False
            if pattern_prefix.endswith('*'):
                prefix = pattern_prefix.rstrip('*')
                matches = key.startswith(prefix)
            else:
                matches = key == pattern_prefix
                
            if matches:
                if len(clauses) == 1:
                    # If it's a single clause, add it directly
                    collected.append(clauses[0])
                else:
                    # IMPORTANT: Within each selection group, use AND logic
                    # This is the key fix - selection groups should use AND between fields
                        collected.append(f"({' AND '.join(clauses)})")
        
        return collected
    except Exception as e:
        logger.error(f"Error in _collect_groups_by_pattern: Failed to collect groups for '{pattern_prefix}'. Error: {str(e)}")
        return []


def _split_condition(condition):
    """Split a complex condition into its components."""
    try:
        parts = []
        current = ''
        depth = 0
        
        for char in condition:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                
            if depth == 0 and char == ' ' and (current.endswith(' and') or current.endswith(' or')):
                if current[:-4].strip():  # Only add if non-empty
                    parts.append(current[:-4].strip())  # Remove the operator
                    parts.append(current[-3:].strip())  # Add the operator
                current = ''
            else:
                current += char
                
        if current and current.strip():  # Only add if non-empty
            parts.append(current.strip())
            
        return parts
    except Exception as e:
        logger.error(f"Error in _split_condition: Failed to split '{condition}'. Error: {str(e)}")
        return [condition]  # Return original as single part on error

def parse_sigma_condition(condition, selection_groups):
    """Parse Sigma condition and build proper Lucene query with selection groups and operator precedence."""
    
    if not condition:
        group_queries = []
        for group_name, clauses in selection_groups.items():
            if len(clauses) == 1:
                group_queries.append(clauses[0])
            else:
                group_queries.append(f"({' AND '.join(clauses)})")
        return " AND ".join(group_queries)

    cond = condition.strip()
    lower = cond.lower()

    # Handle parentheses first
    if cond.startswith('(') and cond.endswith(')') and is_balanced_parentheses(cond):
        inner = cond[1:-1].strip()
        return parse_sigma_condition(inner, selection_groups)

    # Handle 'not' expressions
    if lower.startswith('not '):
        inner = cond[4:].strip()
        positive = parse_sigma_condition(inner, selection_groups)
        if positive:
            return f"NOT ({positive})"

    # Handle "and not" expressions (e.g., "selection and not filter")
    if ' and not ' in lower:
        parts = split_condition_by_operator(cond, ' and not ')
        if len(parts) == 2:
            left_part = parse_sigma_condition(parts[0], selection_groups)
            right_part = parse_sigma_condition(parts[1], selection_groups)
            if left_part and right_part:
                return f"({left_part}) AND NOT ({right_part})"

    # Parse with proper operator precedence: 'and' has higher precedence than 'or'
    # Split by 'or' first (lower precedence)
    or_parts = split_condition_by_operator(cond, ' or ')
    if len(or_parts) > 1:
        expr_parts = []
        for part in or_parts:
            part_result = parse_sigma_condition(part, selection_groups)
            if part_result:
                expr_parts.append(part_result)
        
        if expr_parts:
            if len(expr_parts) == 1:
                return expr_parts[0]
            else:
                return f"({' OR '.join(expr_parts)})"

    # Split by 'and' (higher precedence)
    and_parts = split_condition_by_operator(cond, ' and ')
    if len(and_parts) > 1:
        expr_parts = []
        for part in and_parts:
            part_result = parse_sigma_condition(part, selection_groups)
            if part_result:
                expr_parts.append(part_result)
        
        if expr_parts:
            if len(expr_parts) == 1:
                return expr_parts[0]
            else:
                return f"({' AND '.join(expr_parts)})"

    # Handle atomic elements
    return parse_sigma_atomic_condition(cond, selection_groups)


def parse_sigma_atomic_condition(cond, selection_groups):
    """Parse atomic sigma condition (single group, 1 of pattern, etc.)"""
    cond = cond.strip()
    lower = cond.lower()

    # Handle '1 of' pattern
    if lower.startswith('1 of '):
        pattern = cond[5:].strip()
        collected = _collect_groups_by_pattern(selection_groups, pattern)
        if collected:
            if len(collected) > 1:
                return f"({' OR '.join(collected)})"
            return collected[0]

    # Handle 'all of' pattern  
    if lower.startswith('all of '):
        pattern = cond[7:].strip()
        collected = _collect_groups_by_pattern(selection_groups, pattern)
        if collected:
            return f"({' AND '.join(collected)})"

    # Handle direct group reference
    if cond in selection_groups:
        clauses = selection_groups[cond]
        if len(clauses) == 1:
            return clauses[0]
        else:
            # Multiple clauses in a group should be joined appropriately
            # The logic was already determined in process_field_expression
            # If we have multiple clauses here, they should be AND'ed together
            # because each clause might already be a complex expression
            return f"({' AND '.join(clauses)})"

    return None


def split_condition_by_operator(condition, operator):
    """Split condition by operator, respecting parentheses."""
    parts = []
    current_part = ''
    parentheses_depth = 0
    i = 0
    
    while i < len(condition):
        char = condition[i]
        
        if char == '(':
            parentheses_depth += 1
        elif char == ')':
            parentheses_depth -= 1
        
        # Check if we found the operator at top level
        if (parentheses_depth == 0 and 
            condition[i:i+len(operator)].lower() == operator.lower()):
            parts.append(current_part.strip())
            current_part = ''
            i += len(operator)
            continue
        
        current_part += char
        i += 1
    
    # Add the last part
    if current_part.strip():
        parts.append(current_part.strip())
    
    return parts


def is_balanced_parentheses(text):
    """Check if parentheses are balanced and text is completely wrapped."""
    if not text.startswith('(') or not text.endswith(')'):
        return False
    
    depth = 0
    for i, char in enumerate(text):
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
            # If we close all parentheses before the end, it's not completely wrapped
            if depth == 0 and i < len(text) - 1:
                return False
    
    return depth == 0


def convert_sigma_to_lucene(file_path, rules_dir):
    """Convert Sigma rule to Lucene query format."""
    import os
    if not file_path:
        return Response('No file_path provided', status=400, mimetype='text/plain')
    abs_path = os.path.abspath(os.path.join(rules_dir, file_path))
    if not abs_path.startswith(os.path.abspath(rules_dir)):
        return Response('Forbidden', status=403, mimetype='text/plain')
    if not os.path.exists(abs_path):
        return Response('Not found', status=404, mimetype='text/plain')
    try:
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                return Response(f"Error: Invalid YAML format - {str(e)}", mimetype='text/plain')
            if not data or not isinstance(data, dict):
                return Response("Error: Invalid rule format - must be a YAML dictionary", mimetype='text/plain')
        detection = data.get('detection', {})
        if not detection:
            return Response("Error: No detection section found in rule", mimetype='text/plain')
        selection_groups = process_detection_section(detection)
        condition = detection.get('condition')
        if not selection_groups:
            lucene_query = '# No detection logic found. Check YAML syntax - missing colons after field expressions?'
        else:
            lucene_query = parse_sigma_condition(condition, selection_groups)
        return Response(lucene_query, mimetype='text/plain')
    except Exception as e:
        return Response(f"Error: {str(e)}", mimetype='text/plain')
