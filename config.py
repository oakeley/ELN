import os

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folder for files
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads')
    
    # Neo4j configuration
    NEO4J_URI = os.environ.get('NEO4J_URI') or 'bolt://localhost:7687'
    NEO4J_USER = os.environ.get('NEO4J_USER') or 'neo4j'
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD') or 'password'
    
    # GitHub API token
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN') or ''
    
    # Ollama API configuration
    OLLAMA_API_URL = os.environ.get('OLLAMA_API_URL') or 'http://localhost:11434/api/generate'
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL') or 'mistral-small3.1'
    
    # Stable Diffusion configuration
    STABLE_DIFFUSION_API_URL = os.environ.get('STABLE_DIFFUSION_API_URL') or 'http://localhost:7860/api/predict'
