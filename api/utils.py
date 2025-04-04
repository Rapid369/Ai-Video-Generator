from functools import wraps
from flask import request, jsonify
from flask_restx import abort
import secrets
import string
from app import User

def token_required(f):
    """Decorator to check API key authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if API key is in header
        if 'X-API-KEY' in request.headers:
            token = request.headers['X-API-KEY']
        
        if not token:
            abort(401, 'API key is missing')
        
        # Find user with this API key
        user = User.query.filter_by(api_key=token).first()
        if not user:
            abort(401, 'Invalid API key')
        
        return f(*args, user=user, **kwargs)
    
    return decorated

def generate_api_key(length=32):
    """Generate a random API key"""
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return api_key
