import logging
import logging.handlers
import os
import re
from .config import create_app, ensure_rules_dir, ensure_custom_rules_dir
from .routes import init_routes
from .rules_manager import load_sigma_rules, get_rules
from .deployment_manager import DeploymentManager

def setup_logging():
    """Setup logging configuration for the application."""
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.handlers.RotatingFileHandler(
                os.path.join(logs_dir, 'sigma_app.log'),
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )
    
    # Set specific logger levels
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

def create_application():
    """Create and configure the complete Flask application."""
    import time
    start_time = time.time()
    
    # Setup logging first
    setup_logging()
    logging.info("Starting application initialization...")
    
    try:
        step_start = time.time()
        app = create_app()
        logging.info(f"[OK] Flask app created ({time.time() - step_start:.2f}s)")
        
        # Ensure rules directory exists
        step_start = time.time()
        ensure_rules_dir()
        ensure_custom_rules_dir()
        logging.info(f"[OK] Directories ensured ({time.time() - step_start:.2f}s)")
        
        # Load initial rules
        step_start = time.time()
        load_sigma_rules()
        logging.info(f"[OK] Rules loaded ({time.time() - step_start:.2f}s)")
        
        # Initialize deployment manager
        step_start = time.time()
        deployment_manager = DeploymentManager()
        app.deployment_manager = deployment_manager
        logging.info(f"[OK] Deployment manager initialized ({time.time() - step_start:.2f}s)")
        
        # Clean up old entries khi app khởi động
        step_start = time.time()
        current_rules = get_rules()
        if current_rules:
            existing_paths = [rule['file_path'] for rule in current_rules]
            deployment_manager.clean_old_entries(existing_paths)
        logging.info(f"[OK] Old entries cleaned ({time.time() - step_start:.2f}s)")
        
        # Add custom Jinja2 filter for search highlighting
        @app.template_filter('highlight')
        def highlight_filter(text, query):
            """Highlight search terms in text"""
            if not query or not text:
                return text
            
            # Simple tokenization - split on spaces and remove operators
            terms = []
            for term in query.split():
                # Skip boolean operators and field queries
                if term.upper() not in ['AND', 'OR', 'NOT'] and ':' not in term:
                    # Remove quotes and parentheses
                    clean_term = term.strip('"\'()')
                    if len(clean_term) > 2:  # Only highlight terms longer than 2 chars
                        terms.append(clean_term)
            
            # Highlight each term
            highlighted_text = str(text)
            for term in terms:
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                highlighted_text = pattern.sub(f'<mark>{term}</mark>', highlighted_text)
            
            return highlighted_text
        
        # Initialize routes
        step_start = time.time()
        init_routes(app, get_rules())
        logging.info(f"[OK] Routes initialized ({time.time() - step_start:.2f}s)")
        
        total_time = time.time() - start_time
        logging.info(f"[DONE] Sigma Search Application initialized successfully (Total: {total_time:.2f}s)")
        return app
        
    except Exception as e:
        logging.error(f"Failed to create application: {str(e)}")
        raise
