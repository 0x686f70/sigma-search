from flask import Blueprint, request, jsonify, current_app

def create_deployment_blueprint():
    """Tạo blueprint cho các API liên quan đến deployment"""
    bp = Blueprint('deployment', __name__)

    @bp.route('/api/deployment/status/<path:rule_file_path>', methods=['GET'])
    def get_deployment_status(rule_file_path):
        """Lấy trạng thái triển khai của một rule"""
        try:
            deployment_manager = current_app.deployment_manager
            status = deployment_manager.get_deployment_status(rule_file_path)
            
            return jsonify({
                'success': True,
                'status': status
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/deployment/update', methods=['POST'])
    def update_deployment_status():
        """Cập nhật trạng thái triển khai của một rule"""
        try:
            data = request.get_json()
            
            if not data or 'rule_file_path' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing rule_file_path'
                }), 400
            
            rule_file_path = data['rule_file_path']
            rule_title = data.get('rule_title', '')
            is_deployed = data.get('is_deployed', False)
            notes = data.get('notes', '')
            
            deployment_manager = current_app.deployment_manager
            deployment_manager.update_deployment_status(
                rule_file_path, rule_title, is_deployed, notes
            )
            
            return jsonify({
                'success': True,
                'message': 'Deployment status updated successfully'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/deployment/batch-status', methods=['POST'])
    def get_batch_deployment_status():
        """Lấy trạng thái triển khai của nhiều rules"""
        try:
            data = request.get_json()
            
            if not data or 'rule_file_paths' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing rule_file_paths'
                }), 400
            
            rule_file_paths = data['rule_file_paths']
            deployment_manager = current_app.deployment_manager
            
            results = {}
            for file_path in rule_file_paths:
                status = deployment_manager.get_deployment_status(file_path)
                results[file_path] = status
            
            return jsonify({
                'success': True,
                'results': results
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/deployment/stats', methods=['GET'])
    def get_deployment_stats():
        """Lấy thống kê triển khai"""
        try:
            deployment_manager = current_app.deployment_manager
            stats = deployment_manager.get_deployment_stats()
            
            return jsonify({
                'success': True,
                'stats': stats
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/deployment/filter-stats', methods=['POST'])
    def get_filter_stats():
        """Lấy thống kê cho filter - số lượng deployed/undeployed trong current result set"""
        try:
            from ..rules_manager import get_rules
            from ..rule_loader import search_rules
            
            data = request.get_json()
            current_rules = data.get('current_rules', [])
            
            if not current_rules:
                # Nếu không có rules hiện tại, lấy tất cả rules
                current_rules = [rule['file_path'] for rule in get_rules()]
            
            deployment_manager = current_app.deployment_manager
            deployed_rules = set(deployment_manager.get_deployed_rules())
            
            deployed_count = len([rule for rule in current_rules if rule in deployed_rules])
            undeployed_count = len(current_rules) - deployed_count
            
            return jsonify({
                'success': True,
                'stats': {
                    'total': len(current_rules),
                    'deployed': deployed_count,
                    'undeployed': undeployed_count
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/deployment/create-test-data', methods=['POST'])
    def create_test_data():
        """Tạo test data để demo deployment filter"""
        try:
            from ..rules_manager import get_rules
            
            rules = get_rules()
            if not rules:
                return jsonify({
                    'success': False,
                    'error': 'No rules found'
                }), 400
            
            deployment_manager = current_app.deployment_manager
            
            # Mark first 10 rules as deployed for testing
            test_rules = rules[:10]
            deployed_count = 0
            
            for i, rule in enumerate(test_rules):
                is_deployed = i % 3 == 0  # Mark every 3rd rule as deployed
                if is_deployed:
                    deployment_manager.update_deployment_status(
                        rule['file_path'], 
                        rule['title'], 
                        True,
                        f"Test deployment for demo - {i+1}"
                    )
                    deployed_count += 1
            
            return jsonify({
                'success': True,
                'message': f'Created test data: {deployed_count} rules marked as deployed',
                'deployed_count': deployed_count,
                'total_test_rules': len(test_rules)
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/deployment/deployed-rules', methods=['GET'])
    def get_deployed_rules():
        """Lấy danh sách các rule đã triển khai"""
        try:
            deployment_manager = current_app.deployment_manager
            deployed_rules = deployment_manager.get_deployed_rules()
            
            return jsonify({
                'success': True,
                'deployed_rules': deployed_rules
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    return bp 