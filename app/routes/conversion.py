from flask import request, Blueprint, jsonify
from ..config import get_rules_dir
from ..lucene_converter import convert_sigma_to_lucene
from ..query_parser import parse_lucene_query


def create_conversion_blueprint(rules):
    bp = Blueprint('conversion', __name__)

    @bp.route('/convert_to_lucene')
    def convert_to_lucene_route():
        file_path = request.args.get('file_path')
        rules_dir = get_rules_dir()
        return convert_sigma_to_lucene(file_path, rules_dir)

    @bp.route('/convert_to_structured')
    def convert_to_structured_route():
        file_path = request.args.get('file_path')
        rules_dir = get_rules_dir()
        
        # First get the Lucene query
        lucene_response = convert_sigma_to_lucene(file_path, rules_dir)
        
        if hasattr(lucene_response, 'status_code') and lucene_response.status_code != 200:
            return lucene_response
        
        lucene_query = lucene_response.get_data(as_text=True)
        
        # Parse the Lucene query into structured format
        try:
            structured_query = parse_lucene_query(lucene_query)
            # Add the original query to the response
            if isinstance(structured_query, dict):
                structured_query['original_query'] = lucene_query
            return jsonify(structured_query)
        except Exception as e:
            return jsonify({'error': f'Failed to parse query: {str(e)}', 'original_query': lucene_query}), 400

    return bp


