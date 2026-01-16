"""
Smart CRM Application Factory
"""
import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager

from app.config import Config

login_manager = LoginManager()


def get_cors_origins():
    """Get allowed CORS origins from environment or use defaults."""
    env_origins = os.getenv('CORS_ORIGINS', '')
    if env_origins:
        return [origin.strip() for origin in env_origins.split(',')]

    # Default origins for development
    default_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ]

    # Add Railway domain if RAILWAY_PUBLIC_DOMAIN is set
    railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
    if railway_domain:
        default_origins.append(f"https://{railway_domain}")

    return default_origins


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS for SPA frontend
    CORS(app, resources={
        r"/api/*": {
            "origins": get_cors_origins(),
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.leads import leads_bp
    from app.routes.deals import deals_bp
    from app.routes.tasks import tasks_bp
    from app.routes.analytics import analytics_bp
    from app.routes.chat import chat_bp
    from app.routes.rag import rag_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(leads_bp, url_prefix='/api/leads')
    app.register_blueprint(deals_bp, url_prefix='/api/deals')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(rag_bp, url_prefix='/api/rag')

    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Smart CRM API is running'}

    # Serve frontend pages
    # Allow override via environment variable for deployment flexibility
    frontend_dir = os.getenv('FRONTEND_DIR')
    if not frontend_dir:
        # Default: look for frontend relative to project structure
        # In development: CRM/stitch_representative_crm_dashboard
        # In Railway: /app/stitch_representative_crm_dashboard (if deployed from root)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        frontend_dir = os.path.join(project_root, 'stitch_representative_crm_dashboard')

        # Fallback for Railway deployment from smart-crm subdirectory
        if not os.path.exists(frontend_dir):
            alt_frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend_static')
            if os.path.exists(alt_frontend_dir):
                frontend_dir = alt_frontend_dir

    @app.route('/')
    @app.route('/login')
    def serve_login():
        login_dir = os.path.join(frontend_dir, 'login')
        if os.path.exists(login_dir):
            return send_from_directory(login_dir, 'code.html')
        return {'error': 'Frontend not found', 'hint': 'Set FRONTEND_DIR environment variable'}, 404

    @app.route('/dashboard')
    def serve_dashboard():
        return send_from_directory(os.path.join(frontend_dir, 'representative_crm_dashboard'), 'code.html')

    @app.route('/leads')
    def serve_leads():
        return send_from_directory(os.path.join(frontend_dir, 'lead_management_list'), 'code.html')

    @app.route('/pipeline')
    def serve_pipeline():
        return send_from_directory(os.path.join(frontend_dir, 'sales_pipeline_kanban'), 'code.html')

    @app.route('/lead/<lead_id>')
    def serve_lead_details(lead_id):
        return send_from_directory(os.path.join(frontend_dir, 'lead_details_&_ai_scoring'), 'code.html')

    @app.route('/chat')
    def serve_chat():
        return send_from_directory(os.path.join(frontend_dir, 'multi-mode_customer_chatbot'), 'code.html')

    return app
