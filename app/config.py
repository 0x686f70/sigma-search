import os
import secrets
from flask import Flask

def create_app():
    """Create and configure the Flask application."""
    # Get the project root directory (parent of app directory)
    project_root = os.path.dirname(os.path.dirname(__file__))
    
    app = Flask(__name__, 
                template_folder=os.path.join(project_root, 'templates'),
                static_folder=os.path.join(project_root, 'static'))
    
    # Use environment variable for secret key or generate a secure one
    app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
    
    # Security headers
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    return app

# Global configuration
RULES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sigma_rules')
CUSTOM_RULES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sigma_rules', 'customs')

def get_rules_dir():
    """Get the absolute path to the rules directory."""
    return os.path.abspath(RULES_DIR)

def get_custom_rules_dir():
    """Get the absolute path to the custom rules directory."""
    return os.path.abspath(CUSTOM_RULES_DIR)

def ensure_rules_dir():
    """Ensure the rules directory exists."""
    rules_dir_abs = get_rules_dir()
    if not os.path.exists(rules_dir_abs):
        os.makedirs(rules_dir_abs, exist_ok=True)
    return rules_dir_abs

def ensure_custom_rules_dir():
    """Ensure the custom rules directory exists."""
    custom_rules_dir_abs = get_custom_rules_dir()
    if not os.path.exists(custom_rules_dir_abs):
        os.makedirs(custom_rules_dir_abs, exist_ok=True)
    return custom_rules_dir_abs
