from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
from flask_login import current_user
from app import db, Project
from .utils import token_required

api = Namespace('projects', description='Project operations')

# Define models for documentation
project_model = api.model('Project', {
    'id': fields.Integer(readonly=True, description='The project identifier'),
    'title': fields.String(required=True, description='Project title'),
    'idea': fields.String(description='Project idea/concept'),
    'prompt': fields.String(description='Image/video generation prompt'),
    'status': fields.String(description='Project status'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp')
})

project_input = api.model('ProjectInput', {
    'title': fields.String(required=True, description='Project title'),
    'idea': fields.String(description='Project idea/concept'),
    'prompt': fields.String(description='Image/video generation prompt')
})

@api.route('/')
class ProjectList(Resource):
    @api.doc('list_projects')
    @api.marshal_list_with(project_model)
    @token_required
    def get(self, user):
        """List all projects for the authenticated user"""
        projects = Project.query.filter_by(user_id=user.id).all()
        return projects
    
    @api.doc('create_project')
    @api.expect(project_input)
    @api.marshal_with(project_model, code=201)
    @token_required
    def post(self, user):
        """Create a new project"""
        data = request.json
        
        project = Project(
            title=data['title'],
            idea=data.get('idea'),
            prompt=data.get('prompt'),
            user_id=user.id,
            status='draft'
        )
        
        db.session.add(project)
        db.session.commit()
        
        return project, 201

@api.route('/<int:id>')
@api.param('id', 'The project identifier')
@api.response(404, 'Project not found')
class ProjectResource(Resource):
    @api.doc('get_project')
    @api.marshal_with(project_model)
    @token_required
    def get(self, user, id):
        """Get a project by ID"""
        project = Project.query.get_or_404(id)
        
        # Check if the project belongs to the user
        if project.user_id != user.id:
            api.abort(403, "You don't have permission to access this project")
        
        return project
    
    @api.doc('update_project')
    @api.expect(project_input)
    @api.marshal_with(project_model)
    @token_required
    def put(self, user, id):
        """Update a project"""
        project = Project.query.get_or_404(id)
        
        # Check if the project belongs to the user
        if project.user_id != user.id:
            api.abort(403, "You don't have permission to update this project")
        
        data = request.json
        
        project.title = data.get('title', project.title)
        project.idea = data.get('idea', project.idea)
        project.prompt = data.get('prompt', project.prompt)
        
        db.session.commit()
        
        return project
    
    @api.doc('delete_project')
    @api.response(204, 'Project deleted')
    @token_required
    def delete(self, user, id):
        """Delete a project"""
        project = Project.query.get_or_404(id)
        
        # Check if the project belongs to the user
        if project.user_id != user.id:
            api.abort(403, "You don't have permission to delete this project")
        
        db.session.delete(project)
        db.session.commit()
        
        return '', 204
