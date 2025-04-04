from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
from app import db, Project
from tasks import generate_video_task, generate_idea_task, generate_image_task
from tasks import generate_video_from_image_task, generate_music_task, generate_voice_task
from tasks import create_final_video_task
from .utils import token_required

api = Namespace('generation', description='Video generation operations')

# Define models for documentation
generation_input = api.model('GenerationInput', {
    'project_id': fields.Integer(required=True, description='Project ID'),
    'step': fields.String(description='Generation step (all, idea, image, video, music, voice, final)')
})

generation_output = api.model('GenerationOutput', {
    'task_id': fields.String(description='Task ID for tracking progress'),
    'status': fields.String(description='Task status'),
    'message': fields.String(description='Status message')
})

task_status = api.model('TaskStatus', {
    'status': fields.String(description='Task status'),
    'message': fields.String(description='Status message'),
    'progress': fields.Integer(description='Progress percentage'),
    'step': fields.String(description='Current generation step')
})

@api.route('/generate')
class Generate(Resource):
    @api.doc('generate_video')
    @api.expect(generation_input)
    @api.marshal_with(generation_output)
    @token_required
    def post(self, user):
        """Start a video generation task"""
        data = request.json
        project_id = data.get('project_id')
        step = data.get('step', 'all')
        
        # Validate project
        project = Project.query.get_or_404(project_id)
        
        # Check if the project belongs to the user
        if project.user_id != user.id:
            api.abort(403, "You don't have permission to access this project")
        
        # Update project status
        project.status = 'processing'
        db.session.commit()
        
        # Start the appropriate background task based on the step
        if step == 'all':
            # Generate complete video
            task = generate_video_task.delay(user.id, project_id)
        elif step == 'idea':
            # Generate idea only
            task = generate_idea_task.delay(user.id, project_id)
        elif step == 'image':
            # Generate image only
            task = generate_image_task.delay(user.id, project_id)
        elif step == 'video':
            # Generate video from image
            task = generate_video_from_image_task.delay(user.id, project_id)
        elif step == 'music':
            # Generate music only
            task = generate_music_task.delay(user.id, project_id)
        elif step == 'voice':
            # Generate voice only
            task = generate_voice_task.delay(user.id, project_id)
        elif step == 'final':
            # Create final video
            task = create_final_video_task.delay(user.id, project_id)
        else:
            api.abort(400, "Invalid step")
        
        return {
            'status': 'processing',
            'message': f'Project {step} generation started',
            'task_id': task.id
        }

@api.route('/status/<string:task_id>')
@api.param('task_id', 'The task identifier')
class TaskStatus(Resource):
    @api.doc('get_task_status')
    @api.marshal_with(task_status)
    @token_required
    def get(self, user, task_id):
        """Get the status of a generation task"""
        from celery.result import AsyncResult
        task_result = AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            response = {
                'status': 'pending',
                'message': 'Task is pending',
                'progress': 0,
                'step': ''
            }
        elif task_result.state == 'PROGRESS':
            response = {
                'status': 'processing',
                'message': task_result.info.get('message', 'Processing...'),
                'progress': task_result.info.get('progress', 0),
                'step': task_result.info.get('step', '')
            }
        elif task_result.state == 'SUCCESS':
            result = task_result.result
            response = {
                'status': result.get('status', 'completed'),
                'message': result.get('message', 'Task completed'),
                'progress': 100,
                'step': 'completed'
            }
        else:
            response = {
                'status': 'error',
                'message': str(task_result.result) if task_result.result else 'Unknown error',
                'progress': 0,
                'step': ''
            }
        
        return response
