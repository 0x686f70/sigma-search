import re
from typing import Dict, List, Union, Any
from .field_mappings import get_field_display_name


class QueryNode:
    """Represents a node in the query structure tree."""
    
    def __init__(self, node_type: str, operator: str = None, children: List['QueryNode'] = None, 
                 field: str = None, value: str = None):
        self.node_type = node_type  # 'condition', 'field', 'group'
        self.operator = operator    # 'AND', 'OR', 'NOT'
        self.children = children or []
        self.field = field
        self.value = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the node to a dictionary representation."""
        result = {
            'type': self.node_type,
            'operator': self.operator
        }
        
        if self.field:
            result['field'] = self.field
            # Add display name for better UI
            result['field_display'] = get_field_display_name(self.field)
        if self.value:
            result['value'] = self.value
        if self.children:
            result['children'] = [child.to_dict() for child in self.children]
            
        return result


def parse_lucene_query(query: str) -> Dict[str, Any]:
    """
    Parse a Lucene query string into a structured format.
    
    Args:
        query: The Lucene query string
        
    Returns:
        Dictionary representing the structured query
    """
    if not query or query.strip() == '':
        return {'type': 'empty', 'message': 'No query to parse'}
    
    # Clean up the query
    query = query.strip()
    
    try:
        # Parse the query into a tree structure
        root_node = parse_query_expression(query)
        
        # Convert to dictionary format
        return root_node.to_dict()
        
    except Exception as e:
        return {
            'type': 'error',
            'message': f'Failed to parse query: {str(e)}',
            'original_query': query
        }


def parse_query_expression(expression: str) -> QueryNode:
    """
    Parse a query expression into a QueryNode tree with proper operator precedence.
    
    Precedence (high to low):
    1. Parentheses ()
    2. NOT
    3. AND
    4. OR
    
    Args:
        expression: The query expression to parse
        
    Returns:
        QueryNode representing the parsed expression
    """
    expression = expression.strip()
    
    # Handle NOT expressions first (highest precedence after parentheses)
    if expression.startswith('NOT '):
        inner_expression = expression[4:].strip()
        # Remove outer parentheses if present
        if inner_expression.startswith('(') and inner_expression.endswith(')'):
            inner_expression = inner_expression[1:-1]
        return QueryNode(
            node_type='group',
            operator='NOT',
            children=[parse_query_expression(inner_expression)]
        )
    
    # Handle parentheses groups
    if expression.startswith('(') and expression.endswith(')') and is_complete_parentheses(expression):
        # Remove outer parentheses and parse the inner expression
        inner_expression = expression[1:-1].strip()
        return parse_query_expression(inner_expression)
    
    # Parse with proper operator precedence: OR has lower precedence than AND
    # So we split by OR first (creates the top-level structure)
    or_parts = split_by_operator(expression, ' OR ')
    if len(or_parts) > 1:
        return QueryNode(
            node_type='group',
            operator='OR',
            children=[parse_query_expression(part) for part in or_parts]
        )
    
    # Then split by AND operators (higher precedence)
    and_parts = split_by_operator(expression, ' AND ')
    if len(and_parts) > 1:
        return QueryNode(
            node_type='group',
            operator='AND',
            children=[parse_query_expression(part) for part in and_parts]
        )
    
    # Handle field expressions
    return parse_field_expression(expression)


def parse_field_expression(expression: str) -> QueryNode:
    """
    Parse a field expression like 'field:value' or 'field contains "value"'.
    
    Args:
        expression: The field expression to parse
        
    Returns:
        QueryNode representing the field expression
    """
    expression = expression.strip()
    
    # Handle complex field expressions with operators
    # Pattern: field operator "value" or field operator value
    complex_patterns = [
        # field contains "value"
        (r'^([\w-]+(?:\.[\w-]+)*)\s+(contains|startswith|endswith|equals|is|matches)\s+(.+)$', 'complex_operator'),
        # field:value
        (r'^([\w-]+(?:\.[\w-]+)*):(.+)$', 'colon_format'),
        # field contains value (without quotes)
        (r'^([\w-]+(?:\.[\w-]+)*)\s+(contains|startswith|endswith|equals|is|matches)\s+([^"\s]+)$', 'complex_operator_no_quotes'),
    ]
    
    for pattern, pattern_type in complex_patterns:
        match = re.match(pattern, expression)
        if match:
            if pattern_type == 'complex_operator':
                field = match.group(1)
                operator = match.group(2)
                value = match.group(3).strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                return QueryNode(
                    node_type='condition',
                    operator=operator,
                    field=field,
                    value=value
                )
            elif pattern_type == 'colon_format':
                field = match.group(1)
                value = match.group(2).strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                return QueryNode(
                    node_type='condition',
                    operator='contains',
                    field=field,
                    value=value
                )
            elif pattern_type == 'complex_operator_no_quotes':
                field = match.group(1)
                operator = match.group(2)
                value = match.group(3).strip()
                return QueryNode(
                    node_type='condition',
                    operator=operator,
                    field=field,
                    value=value
                )
    
    # Handle quoted string patterns
    # Pattern: "value" or 'value'
    quoted_match = re.match(r'^["\'](.+)["\']$', expression)
    if quoted_match:
        return QueryNode(
            node_type='condition',
            operator='contains',
            field='text',
            value=quoted_match.group(1)
        )
    
    # Handle wildcard patterns
    # Pattern: *value* or *value or value*
    wildcard_match = re.match(r'^\*(.+)\*$', expression)
    if wildcard_match:
        return QueryNode(
            node_type='condition',
            operator='contains',
            field='text',
            value=wildcard_match.group(1)
        )
    
    # Handle field-only patterns (no value)
    # Pattern: field
    if re.match(r'^\w+(?:\.\w+)*$', expression):
        return QueryNode(
            node_type='condition',
            operator='exists',
            field=expression,
            value=''
        )
    
    # If we can't parse it, return as a raw expression but try to extract field info
    field_info = extract_field_info_from_raw(expression)
    if field_info:
        return QueryNode(
            node_type='condition',
            operator=field_info.get('operator', 'raw'),
            field=field_info.get('field', 'Unknown Field'),
            value=field_info.get('value', expression)
        )
    
    return QueryNode(
        node_type='condition',
        operator='raw',
        value=expression
    )


def extract_field_info_from_raw(expression: str) -> Dict[str, str]:
    """
    Try to extract field information from a raw expression that couldn't be parsed normally.
    
    Args:
        expression: The raw expression to analyze
        
    Returns:
        Dictionary with extracted field, operator, and value information
    """
    # Try to find field patterns in the raw expression
    # Look for patterns like: field ends with "value"
    field_patterns = [
        # Handle the specific pattern from the user's example
        (r'([\w-]+(?:\.[\w-]+)*)\s+\|\s*(contains?|startswith|endswith|equals?|is|matches?)(?:\s*\|\s*(all))?\s*:\s*', 'contains'),
        
        # Standard patterns
        (r'([\w-]+(?:\.[\w-]+)*)\s+(ends?\s+with)\s+["\']([^"\']+)["\']', 'endswith'),
        (r'([\w-]+(?:\.[\w-]+)*)\s+(starts?\s+with)\s+["\']([^"\']+)["\']', 'startswith'),
        (r'([\w-]+(?:\.[\w-]+)*)\s+(contains?)\s+["\']([^"\']+)["\']', 'contains'),
        (r'([\w-]+(?:\.[\w-]+)*)\s+(equals?|is)\s+["\']([^"\']+)["\']', 'equals'),
        (r'([\w-]+(?:\.[\w-]+)*)\s+(ends?\s+with)\s+([^"\s]+)', 'endswith'),
        (r'([\w-]+(?:\.[\w-]+)*)\s+(starts?\s+with)\s+([^"\s]+)', 'startswith'),
        (r'([\w-]+(?:\.[\w-]+)*)\s+(contains?)\s+([^"\s]+)', 'contains'),
        (r'([\w-]+(?:\.[\w-]+)*)\s+(equals?|is)\s+([^"\s]+)', 'equals'),
        
        # Handle field|operator patterns (Sigma specific)
        (r'([\w-]+(?:\.[\w-]+)*)\s*\|\s*(contains?|startswith|endswith|equals?|is|matches?)(?:\s*\|\s*(all))?', 'contains'),
    ]
    
    for pattern, operator in field_patterns:
        match = re.match(pattern, expression, re.IGNORECASE)
        if match:
            if len(match.groups()) >= 3:
                return {
                    'field': match.group(1),
                    'operator': operator,
                    'value': match.group(3)
                }
            else:
                return {
                    'field': match.group(1),
                    'operator': operator,
                    'value': ''
                }
    
    # Try to find field:value patterns
    colon_match = re.match(r'([\w-]+(?:\.[\w-]+)*):(.+)', expression)
    if colon_match:
        value = colon_match.group(2).strip()
        # Remove quotes if present
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        return {
            'field': colon_match.group(1),
            'operator': 'contains',
            'value': value
        }
    
    return None


def split_by_operator(expression: str, operator: str) -> List[str]:
    """
    Split an expression by an operator, respecting parentheses.
    
    Args:
        expression: The expression to split
        operator: The operator to split by (e.g., ' AND ', ' OR ')
        
    Returns:
        List of sub-expressions
    """
    parts = []
    current_part = ''
    parentheses_depth = 0
    quote_depth = 0
    in_quotes = False
    quote_char = None
    
    i = 0
    while i < len(expression):
        char = expression[i]
        
        # Handle quotes
        if char in ['"', "'"]:
            if not in_quotes:
                in_quotes = True
                quote_char = char
                quote_depth += 1
            elif char == quote_char:
                in_quotes = False
                quote_depth -= 1
                if quote_depth == 0:
                    in_quotes = False
        
        # Handle parentheses only when not in quotes
        if not in_quotes:
            if char == '(':
                parentheses_depth += 1
            elif char == ')':
                parentheses_depth -= 1
        
        # Check if we've found the operator at the top level
        if (not in_quotes and parentheses_depth == 0 and 
            expression[i:i+len(operator)] == operator):
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


def is_complete_parentheses(expression: str) -> bool:
    """
    Check if an expression is completely wrapped in parentheses.
    
    Args:
        expression: The expression to check
        
    Returns:
        True if the expression is completely parenthesized
    """
    if not expression.startswith('(') or not expression.endswith(')'):
        return False
    
    parentheses_depth = 0
    for i, char in enumerate(expression):
        if char == '(':
            parentheses_depth += 1
        elif char == ')':
            parentheses_depth -= 1
            # If we close all parentheses before the end, it's not complete
            if parentheses_depth == 0 and i < len(expression) - 1:
                return False
    
    return parentheses_depth == 0 