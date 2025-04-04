from flask import Blueprint
from flask_restx import Api

# Create a Blueprint for the API
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Create a Flask-RESTX API instance
api = Api(
    api_bp,
    version='1.0',
    title='AI Video Generator API',
    description='API for generating AI videos',
    doc='/docs',
    authorizations={
        'apikey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-KEY'
        }
    },
    security='apikey'
)

# Import and register namespaces
from .projects import api as projects_ns
from .users import api as users_ns
from .generation import api as generation_ns

api.add_namespace(projects_ns)
api.add_namespace(users_ns)
api.add_namespace(generation_ns)
