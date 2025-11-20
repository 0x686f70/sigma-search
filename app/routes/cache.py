"""
Cache management routes.
"""
from flask import Blueprint, jsonify
from ..rule_cache import clear_cache
import logging

logger = logging.getLogger(__name__)


def create_cache_blueprint():
    bp = Blueprint('cache', __name__)

    @bp.route('/api/cache/clear', methods=['POST'])
    def clear_cache_route():
        """Clear the rules cache."""
        try:
            success = clear_cache()
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Cache cleared successfully. Restart the application to reload rules.'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to clear cache'
                }), 500
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    return bp
