import os
from flask import abort, Response, request, Blueprint, current_app
from ..config import RULES_DIR


def create_rule_yaml_blueprint(rules):
    bp = Blueprint('rule_yaml', __name__)

    @bp.route('/rule_yaml')
    def rule_yaml():
        file_path = request.args.get('file_path')
        if not file_path:
            return abort(400, description="No file_path provided")
        
        rules_dir = os.path.abspath(RULES_DIR)
        abs_path = os.path.abspath(os.path.join(rules_dir, file_path))
        
        # Security check: ensure path is within rules directory
        if not abs_path.startswith(rules_dir):
            current_app.logger.error(f"Path traversal attempt: {file_path}")
            return abort(403, description="Access denied")
        
        # Check if file exists
        if not os.path.exists(abs_path):
            current_app.logger.error(f"File not found: {abs_path}")
            return abort(404, description=f"File not found: {file_path}")
        
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return Response(content, mimetype='text/plain')
        except UnicodeDecodeError as e:
            current_app.logger.error(f"Unicode decode error for {file_path}: {e}")
            return abort(500, description="File encoding error")
        except Exception as e:
            current_app.logger.error(f"Error serving YAML {file_path}: {e}")
            return abort(500, description="Internal server error")

    return bp


