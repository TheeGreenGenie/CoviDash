import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    FLASK_ENV = os.environ.get('FLASK_ENV') or 'development'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    CDC_API_BASE = os.environ.get('CDC_API_BASE', 'https://data.cdc.gov/resource')
    DISEASE_SH_API = os.environ.get('DISEASE_SH_API', 'https://disease.sh/v3/covid-19')

    UPDATE_INTERVAL_HOURS = int(os.environ.get('UPDATE_INTERVAL_HOURS', 24))

    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = 'UTC'

class DevelopmentConfig(Config):
    DEBUG=True

class ProductionConfig(Config):
    DEBUG = False

app_config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}