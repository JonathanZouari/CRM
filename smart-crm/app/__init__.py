"""
Smart CRM Application Factory
"""
import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager

from app.config import Config

login_manager = LoginManager()


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS for SPA frontend
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5500", "http://127.0.0.1:5500"],
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
    frontend_dir = r'C:\Users\sjzou\OneDrive\Desktop\CRM\stitch_representative_crm_dashboard'

    @app.route('/')
    @app.route('/login')
    def serve_login():
        return send_from_directory(os.path.join(frontend_dir, 'login'), 'code.html')

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
