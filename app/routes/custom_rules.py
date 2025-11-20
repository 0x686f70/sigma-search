import os
import yaml
from flask import jsonify, request, Blueprint, current_app
from ..config import ensure_custom_rules_dir, ensure_rules_dir


def create_custom_rules_blueprint(rules):
    bp = Blueprint('custom_rules', __name__)

    @bp.route('/custom_rules')
    def custom_rules():
        try:
            custom_dir = ensure_custom_rules_dir()
            custom_rules = []
            if os.path.exists(custom_dir):
                for filename in os.listdir(custom_dir):
                    if filename.endswith('.yml') or filename.endswith('.yaml'):
                        file_path = os.path.join(custom_dir, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                rule_data = yaml.safe_load(content)
                                custom_rules.append({
                                    'filename': filename,
                                    'title': rule_data.get('title', filename),
                                    'description': rule_data.get('description', ''),
                                    'tags': rule_data.get('tags', []),
                                    'content': content
                                })
                        except Exception as e:
                            current_app.logger.error(f"Error reading custom rule {filename}: {e}")
            return jsonify(custom_rules)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bp.route('/custom_rules', methods=['POST'])
    def save_custom_rule():
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No JSON data received'}), 400
                
            filename = data.get('filename', '').strip()
            content = data.get('content', '').strip()

            if not filename:
                return jsonify({'error': 'Filename is required'}), 400
                
            if not content:
                return jsonify({'error': 'Content is required'}), 400

            if not filename.endswith('.yml') and not filename.endswith('.yaml'):
                filename += '.yml'

            try:
                parsed = yaml.safe_load(content)
                if parsed is None:
                    return jsonify({'error': 'YAML content is empty or invalid'}), 400
            except yaml.YAMLError as e:
                return jsonify({'error': f'Invalid YAML syntax: {str(e)}'}), 400

            custom_dir = ensure_custom_rules_dir()
            file_path = os.path.join(custom_dir, filename)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Incrementally update in-memory rules (avoid full rescan)
            rules_dir = ensure_rules_dir()
            rel_path = os.path.relpath(file_path, rules_dir).replace(os.sep, '/')
            rule_entry = {
                'title': parsed.get('title', '') if isinstance(parsed, dict) else '',
                'description': parsed.get('description', '') if isinstance(parsed, dict) else '',
                'tags': parsed.get('tags', []) if isinstance(parsed, dict) and isinstance(parsed.get('tags'), list) else [],
                'file_path': rel_path,
                'logsource': parsed.get('logsource', {}) if isinstance(parsed, dict) and isinstance(parsed.get('logsource'), dict) else {},
                'content': content
            }

            replaced = False
            for i, existing in enumerate(rules):
                if existing.get('file_path') == rel_path:
                    rules[i] = rule_entry
                    replaced = True
                    break
            if not replaced:
                rules.append(rule_entry)

            return jsonify({'success': True, 'message': 'Rule saved successfully', 'file_path': rel_path, 'title': rule_entry['title']})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bp.route('/custom_rules/<filename>', methods=['DELETE'])
    def delete_custom_rule(filename):
        try:
            custom_dir = ensure_custom_rules_dir()
            file_path = os.path.join(custom_dir, filename)

            if not os.path.exists(file_path):
                return jsonify({'error': 'File not found'}), 404

            os.remove(file_path)

            # Incrementally update in-memory rules to reflect deletion
            rules_dir = ensure_rules_dir()
            rel_path = os.path.relpath(file_path, rules_dir).replace(os.sep, '/')
            # Remove any entries matching this file path
            remaining = [r for r in rules if r.get('file_path') != rel_path]
            rules.clear()
            rules.extend(remaining)

            return jsonify({'success': True, 'message': 'Rule deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return bp


