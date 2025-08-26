from flask import Flask
from flask_bootstrap import Bootstrap
from flask_wtf import CSRFProtect

# Initialize Flask extensions
bootstrap = Bootstrap()
csrf = CSRFProtect()

def create_app(config_name='default'):
    """Create and configure the Flask application"""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Load configuration
    from app.config.config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    bootstrap.init_app(app)
    csrf.init_app(app)
    
    # Register blueprints
    from app.controllers.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Create database tables
    with app.app_context():
        from app.models.db import init_db
        init_db()
    
    return app
