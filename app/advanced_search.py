import re
import yaml
from datetime import datetime

class AdvancedSearchParser:
    """
    Advanced search parser for Sigma rules with support for:
    - Field-specific search: author:Nextron, date:2025, modified:2025
    - Boolean operators: AND, OR, NOT
    - Parentheses grouping: (date:2025 OR modified:2025)
    - Complex queries: Nextron Systems AND (date:2025 OR modified:2025)
    """
    
    def __init__(self):
        self.field_mappings = {
            'title': lambda rule: rule.get('title', ''),
            'description': lambda rule: rule.get('description', ''),
            'author': self._extract_author,
            'date': self._extract_date,
            'modified': self._extract_modified,
            'tags': lambda rule: ' '.join(rule.get('tags', [])),
            'id': self._extract_id,
            'status': self._extract_status,
            'level': self._extract_level,
            'product': lambda rule: rule.get('logsource', {}).get('product', ''),
            'category': lambda rule: rule.get('logsource', {}).get('category', ''),
            'service': lambda rule: rule.get('logsource', {}).get('service', ''),
            'content': lambda rule: rule.get('content', ''),
            'filename': lambda rule: rule.get('file_path', '').split('/')[-1],
            'path': lambda rule: rule.get('file_path', '')
        }
    
    def _extract_author(self, rule):
        """Extract author from YAML content"""
        try:
            content = rule.get('content', '')
            if 'author:' in content:
                for line in content.split('\n'):
                    if line.strip().startswith('author:'):
                        author = line.split('author:', 1)[1].strip()
                        # Remove quotes if present
                        author = author.strip('"\'')
                        return author
        except:
            pass
        return ''
    
    def _extract_date(self, rule):
        """Extract date from YAML content"""
        try:
            content = rule.get('content', '')
            if 'date:' in content:
                for line in content.split('\n'):
                    if line.strip().startswith('date:'):
                        date = line.split('date:', 1)[1].strip()
                        return date.strip('"\'')
        except:
            pass
        return ''
    
    def _extract_modified(self, rule):
        """Extract modified date from YAML content"""
        try:
            content = rule.get('content', '')
            if 'modified:' in content:
                for line in content.split('\n'):
                    if line.strip().startswith('modified:'):
                        modified = line.split('modified:', 1)[1].strip()
                        return modified.strip('"\'')
        except:
            pass
        return ''
    
    def _extract_id(self, rule):
        """Extract rule ID from YAML content"""
        try:
            content = rule.get('content', '')
            if 'id:' in content:
                for line in content.split('\n'):
                    if line.strip().startswith('id:'):
                        rule_id = line.split('id:', 1)[1].strip()
                        return rule_id.strip('"\'')
        except:
            pass
        return ''
    
    def _extract_status(self, rule):
        """Extract status from YAML content"""
        try:
            content = rule.get('content', '')
            if 'status:' in content:
                for line in content.split('\n'):
                    if line.strip().startswith('status:'):
                        status = line.split('status:', 1)[1].strip()
                        return status.strip('"\'')
        except:
            pass
        return ''
    
    def _extract_level(self, rule):
        """Extract level from YAML content"""
        try:
            content = rule.get('content', '')
            if 'level:' in content:
                for line in content.split('\n'):
                    if line.strip().startswith('level:'):
                        level = line.split('level:', 1)[1].strip()
                        return level.strip('"\'')
        except:
            pass
        return ''
    
    def _tokenize(self, query):
        """Tokenize the search query into components"""
        # Handle parentheses by adding spaces around them
        query = re.sub(r'([()])', r' \1 ', query)
        
        # Split on whitespace while preserving quoted strings
        tokens = []
        current_token = ''
        in_quotes = False
        quote_char = None
        
        i = 0
        while i < len(query):
            char = query[i]
            
            if char in ['"', "'"] and not in_quotes:
                in_quotes = True
                quote_char = char
                # Don't include quote in token for cleaner processing
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
                # Don't include quote in token
            elif char.isspace() and not in_quotes:
                if current_token.strip():
                    tokens.append(current_token.strip())
                current_token = ''
            else:
                current_token += char
            
            i += 1
        
        if current_token.strip():
            tokens.append(current_token.strip())
        
        # Handle field: value with spaces (like "date: 2025")
        combined_tokens = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # Check if current token ends with ':' and next token is a value
            if (token.endswith(':') and 
                i + 1 < len(tokens) and 
                tokens[i + 1].upper() not in {'AND', 'OR', 'NOT', '(', ')'}):
                # Combine field: and value
                combined_tokens.append(token + tokens[i + 1])
                i += 2  # Skip next token since we combined it
            else:
                combined_tokens.append(token)
                i += 1
        
        # Handle implicit AND between consecutive non-operator tokens
        processed_tokens = []
        operators = {'AND', 'OR', 'NOT', '(', ')'}
        
        for i, token in enumerate(combined_tokens):
            processed_tokens.append(token)
            
            # Add implicit AND if current token is not an operator
            # and next token exists and is not an operator
            if (i < len(combined_tokens) - 1 and 
                token.upper() not in operators and
                combined_tokens[i + 1].upper() not in operators):
                processed_tokens.append('AND')
        
        return processed_tokens
    
    def _parse_field_query(self, term):
        """Parse field:value queries"""
        if ':' in term and not term.startswith('http'):
            field, value = term.split(':', 1)
            field = field.strip().lower()
            value = value.strip().strip('"\'')
            # Handle empty value after colon (like "date: " followed by separate token)
            if not value:
                return None, term
            return field, value
        return None, term
    
    def _match_rule_field(self, rule, field, value):
        """Check if a rule matches a specific field:value query"""
        if field not in self.field_mappings:
            # If field not recognized, search in content
            field_content = rule.get('content', '').lower()
            return value.lower() in field_content
        
        field_content = self.field_mappings[field](rule).lower()
        value_lower = value.lower()
        
        # Special handling for date fields - more precise matching
        if field in ['date', 'modified']:
            # For dates, check if the value appears as a year or in date format
            if len(value) == 4 and value.isdigit():  # Year search like "2025"
                # Look for year in date format (YYYY-MM-DD or YYYY/MM/DD)
                return (f"{value}-" in field_content or 
                        f"{value}/" in field_content or 
                        field_content.startswith(value) or
                        f" {value}" in field_content)
            else:
                # Exact substring match for other date formats
                return value_lower in field_content
        
        return value_lower in field_content
    
    def _match_rule_general(self, rule, term):
        """General search across all common fields"""
        term_lower = term.lower()
        
        # Search in common fields
        searchable_content = [
            rule.get('title', ''),
            rule.get('description', ''),
            ' '.join(rule.get('tags', [])),
            rule.get('content', ''),
            self._extract_author(rule),
            rule.get('file_path', '')
        ]
        
        return any(term_lower in content.lower() for content in searchable_content)
    
    def _evaluate_expression(self, tokens, rules):
        """Evaluate a boolean expression with parentheses support"""
        # Convert infix to postfix notation (Shunting Yard algorithm)
        output_queue = []
        operator_stack = []
        
        precedence = {'OR': 1, 'AND': 2, 'NOT': 3}
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token.upper() in ['AND', 'OR', 'NOT']:
                while (operator_stack and 
                       operator_stack[-1] != '(' and
                       operator_stack[-1].upper() in precedence and
                       precedence.get(operator_stack[-1].upper(), 0) >= precedence[token.upper()]):
                    output_queue.append(operator_stack.pop())
                operator_stack.append(token.upper())
            elif token == '(':
                operator_stack.append(token)
            elif token == ')':
                while operator_stack and operator_stack[-1] != '(':
                    output_queue.append(operator_stack.pop())
                if operator_stack:  # Remove the '('
                    operator_stack.pop()
            else:
                output_queue.append(token)
            
            i += 1
        
        while operator_stack:
            output_queue.append(operator_stack.pop())
        
        # Evaluate postfix expression
        results = []
        for rule in rules:
            stack = []
            
            for token in output_queue:
                if token.upper() in ['AND', 'OR', 'NOT']:
                    if token.upper() == 'NOT':
                        if stack:
                            operand = stack.pop()
                            stack.append(not operand)
                    else:
                        if len(stack) >= 2:
                            right = stack.pop()
                            left = stack.pop()
                            if token.upper() == 'AND':
                                stack.append(left and right)
                            elif token.upper() == 'OR':
                                stack.append(left or right)
                else:
                    # Evaluate term against rule
                    field, value = self._parse_field_query(token)
                    if field:
                        match = self._match_rule_field(rule, field, value)
                    else:
                        match = self._match_rule_general(rule, value)
                    stack.append(match)
            
            if stack and stack[0]:
                results.append(rule)
        
        return results
    
    def search(self, rules, query):
        """
        Main search function
        
        Examples:
        - "Nextron Systems AND (date:2025 OR modified:2025)"
        - "author:Nextron AND level:high"
        - "mimikatz OR (powershell AND execution)"
        - "product:windows AND NOT status:experimental"
        """
        if not query or not query.strip():
            return rules
        
        query = query.strip()
        
        # Tokenize the query
        tokens = self._tokenize(query)
        
        if not tokens:
            return rules
        
        # If no boolean operators or parentheses, fall back to simple search
        has_operators = any(token.upper() in ['AND', 'OR', 'NOT'] for token in tokens)
        has_parentheses = any(token in ['(', ')'] for token in tokens)
        
        if not has_operators and not has_parentheses:
            # Simple search across all fields
            term = query.strip()
            field, value = self._parse_field_query(term)
            
            results = []
            for rule in rules:
                if field:
                    if self._match_rule_field(rule, field, value):
                        results.append(rule)
                else:
                    if self._match_rule_general(rule, value):
                        results.append(rule)
            return results
        
        # Complex search with boolean logic
        return self._evaluate_expression(tokens, rules)

# Create global instance
advanced_search = AdvancedSearchParser()

def search_rules_advanced(rules, query):
    """
    Advanced search function that replaces the simple search_rules
    """
    return advanced_search.search(rules, query) 