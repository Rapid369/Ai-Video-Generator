from celery import Celery
from flask import current_app
from services.video_generation import VideoGenerationService
import os

# Initialize Celery
celery = Celery('ai_video_generator')

# Configure Celery
celery.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@celery.task(bind=True)
def generate_video_task(self, user_id, project_id):
    """Background task to generate a complete video."""
    from app import app, db, User, Project
    
    with app.app_context():
        # Get user and project from database
        user = User.query.get(user_id)
        project = Project.query.get(project_id)
        
        if not user or not project:
            return {
                'status': 'error',
                'message': 'User or project not found'
            }
        
        # Initialize video generation service
        service = VideoGenerationService(user=user, project=project)
        
        # Update task state to indicate progress
        self.update_state(state='PROGRESS', meta={'status': 'processing', 'step': 'idea'})
        
        try:
            # Step 1: Generate idea
            result = service.generate_idea()
            idea, prompt = result["idea"], result["prompt"]
            db.session.commit()
            
            self.update_state(state='PROGRESS', meta={'status': 'processing', 'step': 'image', 'progress': 20})
            
            # Step 2: Generate image
            image_path = service.generate_image(prompt)
            db.session.commit()
            
            self.update_state(state='PROGRESS', meta={'status': 'processing', 'step': 'voice', 'progress': 40})
            
            # Step 3: Generate voice dialog
            voice_data = service.generate_voice_dialog(idea)
            db.session.commit()
            
            self.update_state(state='PROGRESS', meta={'status': 'processing', 'step': 'video', 'progress': 60})
            
            # Step 4: Generate video
            video_path = service.generate_video(image_path, prompt)
            db.session.commit()
            
            self.update_state(state='PROGRESS', meta={'status': 'processing', 'step': 'music', 'progress': 80})
            
            # Step 5: Generate music
            music_path = service.generate_music(idea)
            db.session.commit()
            
            self.update_state(state='PROGRESS', meta={'status': 'processing', 'step': 'final', 'progress': 90})
            
            # Step 6: Create final video with music and voice
            final_video = service.create_final_video(video_path, music_path, idea, voice_data)
            
            # Update project status
            project.status = 'completed'
            db.session.commit()
            
            return {
                'status': 'completed',
                'message': 'Video generation completed successfully',
                'final_video': final_video
            }
        except Exception as e:
            # Update project status
            project.status = 'error'
            db.session.commit()
            
            return {
                'status': 'error',
                'message': str(e)
            }

@celery.task
def generate_idea_task(user_id, project_id):
    """Background task to generate an idea."""
    from app import app, db, User, Project
    
    with app.app_context():
        # Get user and project from database
        user = User.query.get(user_id)
        project = Project.query.get(project_id)
        
        if not user or not project:
            return {
                'status': 'error',
                'message': 'User or project not found'
            }
        
        # Initialize video generation service
        service = VideoGenerationService(user=user, project=project)
        
        try:
            # Generate idea
            result = service.generate_idea()
            
            # Update project status
            project.status = 'draft'
            db.session.commit()
            
            return {
                'status': 'completed',
                'message': 'Idea generation completed successfully',
                'idea': result['idea'],
                'prompt': result['prompt']
            }
        except Exception as e:
            # Update project status
            project.status = 'error'
            db.session.commit()
            
            return {
                'status': 'error',
                'message': str(e)
            }

@celery.task
def generate_image_task(user_id, project_id):
    """Background task to generate an image."""
    from app import app, db, User, Project
    
    with app.app_context():
        # Get user and project from database
        user = User.query.get(user_id)
        project = Project.query.get(project_id)
        
        if not user or not project:
            return {
                'status': 'error',
                'message': 'User or project not found'
            }
        
        # Initialize video generation service
        service = VideoGenerationService(user=user, project=project)
        
        try:
            # Generate image
            image_path = service.generate_image(project.prompt)
            
            # Update project status
            project.status = 'draft'
            db.session.commit()
            
            return {
                'status': 'completed',
                'message': 'Image generation completed successfully',
                'image_path': image_path
            }
        except Exception as e:
            # Update project status
            project.status = 'error'
            db.session.commit()
            
            return {
                'status': 'error',
                'message': str(e)
            }

@celery.task
def generate_video_from_image_task(user_id, project_id):
    """Background task to generate a video from an image."""
    from app import app, db, User, Project
    
    with app.app_context():
        # Get user and project from database
        user = User.query.get(user_id)
        project = Project.query.get(project_id)
        
        if not user or not project:
            return {
                'status': 'error',
                'message': 'User or project not found'
            }
        
        # Initialize video generation service
        service = VideoGenerationService(user=user, project=project)
        
        try:
            # Generate video
            video_path = service.generate_video(f"static/{project.image_path}", project.prompt)
            
            # Update project status
            project.status = 'draft'
            db.session.commit()
            
            return {
                'status': 'completed',
                'message': 'Video generation completed successfully',
                'video_path': video_path
            }
        except Exception as e:
            # Update project status
            project.status = 'error'
            db.session.commit()
            
            return {
                'status': 'error',
                'message': str(e)
            }

@celery.task
def generate_music_task(user_id, project_id):
    """Background task to generate music."""
    from app import app, db, User, Project
    
    with app.app_context():
        # Get user and project from database
        user = User.query.get(user_id)
        project = Project.query.get(project_id)
        
        if not user or not project:
            return {
                'status': 'error',
                'message': 'User or project not found'
            }
        
        # Initialize video generation service
        service = VideoGenerationService(user=user, project=project)
        
        try:
            # Generate music
            music_path = service.generate_music(project.idea)
            
            # Update project status
            project.status = 'draft'
            db.session.commit()
            
            return {
                'status': 'completed',
                'message': 'Music generation completed successfully',
                'music_path': music_path
            }
        except Exception as e:
            # Update project status
            project.status = 'error'
            db.session.commit()
            
            return {
                'status': 'error',
                'message': str(e)
            }

@celery.task
def generate_voice_task(user_id, project_id):
    """Background task to generate voice narration."""
    from app import app, db, User, Project
    
    with app.app_context():
        # Get user and project from database
        user = User.query.get(user_id)
        project = Project.query.get(project_id)
        
        if not user or not project:
            return {
                'status': 'error',
                'message': 'User or project not found'
            }
        
        # Initialize video generation service
        service = VideoGenerationService(user=user, project=project)
        
        try:
            # Generate voice
            voice_data = service.generate_voice_dialog(project.idea)
            
            # Update project status
            project.status = 'draft'
            db.session.commit()
            
            return {
                'status': 'completed',
                'message': 'Voice generation completed successfully',
                'voice_path': voice_data['filename'],
                'script': voice_data['script']
            }
        except Exception as e:
            # Update project status
            project.status = 'error'
            db.session.commit()
            
            return {
                'status': 'error',
                'message': str(e)
            }

@celery.task
def create_final_video_task(user_id, project_id):
    """Background task to create the final video."""
    from app import app, db, User, Project
    
    with app.app_context():
        # Get user and project from database
        user = User.query.get(user_id)
        project = Project.query.get(project_id)
        
        if not user or not project:
            return {
                'status': 'error',
                'message': 'User or project not found'
            }
        
        # Initialize video generation service
        service = VideoGenerationService(user=user, project=project)
        
        try:
            # Create final video
            voice_data = {
                'filename': f"static/{project.voice_path}",
                'script': ''  # We don't need the script here
            }
            
            final_video = service.create_final_video(
                f"static/{project.video_path}",
                f"static/{project.music_path}",
                project.idea,
                voice_data
            )
            
            # Update project status
            project.status = 'completed'
            db.session.commit()
            
            return {
                'status': 'completed',
                'message': 'Final video creation completed successfully',
                'final_video': final_video
            }
        except Exception as e:
            # Update project status
            project.status = 'error'
            db.session.commit()
            
            return {
                'status': 'error',
                'message': str(e)
            }
