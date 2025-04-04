from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
from app import db, User
from werkzeug.security import generate_password_hash
from .utils import token_required, generate_api_key

api = Namespace('users', description='User operations')

# Define models for documentation
user_model = api.model('User', {
    'id': fields.Integer(readonly=True, description='The user identifier'),
    'email': fields.String(required=True, description='User email'),
    'name': fields.String(description='User name'),
    'subscription_tier': fields.String(description='Subscription tier'),
    'created_at': fields.DateTime(description='Account creation timestamp')
})

user_input = api.model('UserInput', {
    'email': fields.String(required=True, description='User email'),
    'password': fields.String(required=True, description='User password'),
    'name': fields.String(description='User name')
})

api_key_model = api.model('ApiKey', {
    'api_key': fields.String(description='API key for authentication')
})

@api.route('/me')
class UserProfile(Resource):
    @api.doc('get_user_profile')
    @api.marshal_with(user_model)
    @token_required
    def get(self, user):
        """Get the authenticated user's profile"""
        return user
    
    @api.doc('update_user_profile')
    @api.expect(user_input)
    @api.marshal_with(user_model)
    @token_required
    def put(self, user):
        """Update the authenticated user's profile"""
        data = request.json
        
        if 'email' in data:
            # Check if email is already taken
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user.id:
                api.abort(400, "Email already in use")
            user.email = data['email']
        
        if 'name' in data:
            user.name = data['name']
        
        if 'password' in data:
            user.password_hash = generate_password_hash(data['password'])
        
        db.session.commit()
        
        return user

@api.route('/api-key')
class ApiKey(Resource):
    @api.doc('get_api_key')
    @api.marshal_with(api_key_model)
    @token_required
    def get(self, user):
        """Get the user's API key"""
        # If user doesn't have an API key, generate one
        if not hasattr(user, 'api_key') or not user.api_key:
            user.api_key = generate_api_key()
            db.session.commit()
        
        return {'api_key': user.api_key}
    
    @api.doc('regenerate_api_key')
    @api.marshal_with(api_key_model)
    @token_required
    def post(self, user):
        """Regenerate the user's API key"""
        user.api_key = generate_api_key()
        db.session.commit()
        
        return {'api_key': user.api_key}
