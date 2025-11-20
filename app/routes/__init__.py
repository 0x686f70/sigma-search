from .main import create_main_blueprint
from .update import create_update_blueprint
from .custom_rules import create_custom_rules_blueprint
from .rule_yaml import create_rule_yaml_blueprint
from .conversion import create_conversion_blueprint
from .deployment import create_deployment_blueprint
from .search import create_search_blueprint
from .cache import create_cache_blueprint
import logging

logger = logging.getLogger(__name__)

def init_routes(app, rules):
    """Initialize all application routes."""
    try:
        app.register_blueprint(create_main_blueprint(rules))
        app.register_blueprint(create_update_blueprint(rules))
        app.register_blueprint(create_custom_rules_blueprint(rules))
        app.register_blueprint(create_rule_yaml_blueprint(rules))
        app.register_blueprint(create_conversion_blueprint(rules))
        app.register_blueprint(create_deployment_blueprint())
        app.register_blueprint(create_search_blueprint())
        app.register_blueprint(create_cache_blueprint())
        
        logger.info("All routes initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize routes: {str(e)}")
        raise


