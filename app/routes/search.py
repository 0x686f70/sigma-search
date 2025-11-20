from flask import Blueprint, request, jsonify, current_app
from ..advanced_search import search_rules_advanced
import logging

def create_search_blueprint():
    """Tạo blueprint cho các API search"""
    bp = Blueprint('search', __name__)

    @bp.route('/api/search/custom-rules', methods=['POST'])
    def search_custom_rules():
        """Advanced search cho custom rules"""
        try:
            data = request.get_json()
            
            if not data or 'query' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing query parameter'
                }), 400
            
            query = data['query'].strip()
            rules = data.get('rules', [])
            
            if not query:
                return jsonify({
                    'success': True,
                    'results': rules,
                    'query': query
                })
            
            # Convert custom rules format to standard format for advanced search
            converted_rules = []
            for rule in rules:
                # Map custom rules structure to standard sigma rules structure
                converted_rule = {
                    'title': rule.get('title', ''),
                    'description': rule.get('description', ''),
                    'tags': rule.get('tags', []),
                    'file_path': rule.get('filename', ''),
                    'content': rule.get('content', ''),  # Full YAML content if available
                    'logsource': rule.get('logsource', {}),
                    # Add other fields that might be in custom rules
                    'author': rule.get('author', ''),
                    'date': rule.get('date', ''),
                    'modified': rule.get('modified', ''),
                    'status': rule.get('status', ''),
                    'level': rule.get('level', ''),
                    'id': rule.get('id', '')
                }
                converted_rules.append(converted_rule)
            
            # Use advanced search
            filtered_results = search_rules_advanced(converted_rules, query)
            
            # Convert back to custom rules format
            final_results = []
            for result in filtered_results:
                # Find original rule by filename/title match
                original_rule = None
                for original in rules:
                    if (original.get('filename') == result.get('file_path') or 
                        original.get('title') == result.get('title')):
                        original_rule = original
                        break
                
                if original_rule:
                    final_results.append(original_rule)
                else:
                    # Fallback: create from converted data
                    final_results.append({
                        'filename': result.get('file_path', ''),
                        'title': result.get('title', ''),
                        'description': result.get('description', ''),
                        'tags': result.get('tags', []),
                        'content': result.get('content', ''),
                        'author': result.get('author', ''),
                        'date': result.get('date', ''),
                        'modified': result.get('modified', ''),
                        'status': result.get('status', ''),
                        'level': result.get('level', ''),
                        'id': result.get('id', '')
                    })
            
            return jsonify({
                'success': True,
                'results': final_results,
                'query': query,
                'total_found': len(final_results),
                'search_type': 'advanced'
            })
            
        except Exception as e:
            logging.error(f"Error in custom rules search: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Search error: {str(e)}',
                'search_type': 'failed'
            }), 500

    return bp 