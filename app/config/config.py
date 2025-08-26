import os

basedir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class Config:
    """Base configuration settings"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'school-nurse-health-log-secret-key'
    DB_FILE = os.path.join(basedir, 'instance', 'nurse_records.db')
    EXCEL_FILE = os.path.join(basedir, 'SchoolNurse_HealthLog.xlsx')
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Development configuration settings"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration settings"""
    DEBUG = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
