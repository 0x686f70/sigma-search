import os
import logging
from flask import request
from app import create_application

# Create the Flask application
app = create_application()

# --- Logging setup ---
# Đảm bảo Werkzeug log luôn hiện ra
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.INFO)

# Middleware log request thủ công
@app.before_request
def log_request():
    print(f"[REQUEST] {request.method} {request.path} from {request.remote_addr}")

if __name__ == '__main__':
    # Get configuration from environment variables
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'  # Default to True for development
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))

    # Run the application
    app.run(
        debug=debug_mode,
        host=host,
        port=port,
        threaded=True,
        use_reloader=debug_mode  # Enable auto-reload in debug mode
    )
#heheh