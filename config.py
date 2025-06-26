import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'website_analyzer.db'
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

    # Updated Gemini API specific settings - using current free model
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL') or 'gemini-1.5-flash'
    GEMINI_TEMPERATURE = float(os.environ.get('GEMINI_TEMPERATURE', '0.3'))
    GEMINI_MAX_TOKENS = int(os.environ.get('GEMINI_MAX_TOKENS', '2000'))

    # Application settings
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    RATE_LIMIT = os.environ.get('RATE_LIMIT', '100 per hour')

    # Database settings
    DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', '10'))
    DB_TIMEOUT = int(os.environ.get('DB_TIMEOUT', '30'))

    # Crawler settings
    CRAWLER_TIMEOUT = int(os.environ.get('CRAWLER_TIMEOUT', '30'))
    CRAWLER_MAX_PAGES = int(os.environ.get('CRAWLER_MAX_PAGES', '1'))
    CRAWLER_USER_AGENT = os.environ.get('CRAWLER_USER_AGENT', 'AI Website Analyzer Bot/1.0')

    @classmethod
    def validate_config(cls):
        """Validate required configuration variables"""
        errors = []

        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required but not set")

        if cls.GEMINI_TEMPERATURE < 0 or cls.GEMINI_TEMPERATURE > 1:
            errors.append("GEMINI_TEMPERATURE must be between 0 and 1")

        if cls.GEMINI_MAX_TOKENS < 100:
            errors.append("GEMINI_MAX_TOKENS must be at least 100")

        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"- {error}" for error in errors))

        return True

    @classmethod
    def get_gemini_config(cls):
        """Get Gemini-specific configuration as a dictionary"""
        return {
            'api_key': cls.GEMINI_API_KEY,
            'model': cls.GEMINI_MODEL,
            'temperature': cls.GEMINI_TEMPERATURE,
            'max_tokens': cls.GEMINI_MAX_TOKENS
        }