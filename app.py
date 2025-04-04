import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv
from tasks import generate_video_task, generate_idea_task, generate_image_task, generate_video_from_image_task, generate_music_task, generate_voice_task, create_final_video_task

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///aivideo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    openai_api_key = db.Column(db.String(100), nullable=True)
    replicate_api_key = db.Column(db.String(100), nullable=True)
    sonauto_api_key = db.Column(db.String(100), nullable=True)
    subscription_tier = db.Column(db.String(20), default='free')
    api_key = db.Column(db.String(64), unique=True, nullable=True)
    projects = db.relationship('Project', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Define Project model
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    idea = db.Column(db.Text, nullable=True)
    prompt = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(255), nullable=True)
    video_path = db.Column(db.String(255), nullable=True)
    music_path = db.Column(db.String(255), nullable=True)
    voice_path = db.Column(db.String(255), nullable=True)
    final_video_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.created_at.desc()).all()
    return render_template('dashboard.html', projects=projects)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already registered')
            return redirect(url_for('register'))

        new_user = User(email=email, name=name)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'POST':
        # Update API keys
        current_user.openai_api_key = request.form.get('openai_api_key')
        current_user.replicate_api_key = request.form.get('replicate_api_key')
        current_user.sonauto_api_key = request.form.get('sonauto_api_key')

        # Update name
        current_user.name = request.form.get('name')

        db.session.commit()
        flash('Account updated successfully')

    return render_template('account.html')

@app.route('/new-project', methods=['GET', 'POST'])
@login_required
def new_project():
    if request.method == 'POST':
        title = request.form.get('title')

        project = Project(
            title=title,
            user_id=current_user.id,
            status='draft'
        )

        db.session.add(project)
        db.session.commit()

        return redirect(url_for('edit_project', project_id=project.id))

    return render_template('new_project.html')

@app.route('/project/<int:project_id>')
@login_required
def view_project(project_id):
    project = Project.query.get_or_404(project_id)

    # Check if the project belongs to the current user
    if project.user_id != current_user.id:
        flash('You do not have permission to view this project')
        return redirect(url_for('dashboard'))

    return render_template('view_project.html', project=project)

@app.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)

    # Check if the project belongs to the current user
    if project.user_id != current_user.id:
        flash('You do not have permission to edit this project')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        project.title = request.form.get('title')
        project.idea = request.form.get('idea')
        project.prompt = request.form.get('prompt')

        db.session.commit()
        flash('Project updated successfully')

    return render_template('edit_project.html', project=project)

@app.route('/project/<int:project_id>/generate', methods=['POST'])
@login_required
def generate_project(project_id):
    project = Project.query.get_or_404(project_id)

    # Check if the project belongs to the current user
    if project.user_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403

    # Get the generation step from the request
    step = request.json.get('step', 'all')

    # Update project status
    project.status = 'processing'
    db.session.commit()

    # For demo purposes, we'll run the generation directly instead of using Celery
    from services.video_generation import VideoGenerationService
    service = VideoGenerationService(user=current_user, project=project)

    try:
        if step == 'all':
            # Generate complete video
            result = service.generate_complete_video()
        elif step == 'idea':
            # Generate idea only
            result = service.generate_idea()
            project.status = 'draft'
        elif step == 'image':
            # Generate image only
            image_path = service.generate_image(project.prompt)
            project.status = 'draft'
            result = {'status': 'completed', 'message': 'Image generated successfully'}
        elif step == 'video':
            # Generate video from image
            video_path = service.generate_video(f"static/{project.image_path}", project.prompt)
            project.status = 'draft'
            result = {'status': 'completed', 'message': 'Video generated successfully'}
        elif step == 'music':
            # Generate music only
            music_path = service.generate_music(project.idea)
            project.status = 'draft'
            result = {'status': 'completed', 'message': 'Music generated successfully'}
        elif step == 'voice':
            # Generate voice only
            voice_data = service.generate_voice_dialog(project.idea)
            project.status = 'draft'
            result = {'status': 'completed', 'message': 'Voice generated successfully'}
        elif step == 'final':
            # Create final video
            final_video = service.create_final_video(
                f"static/{project.video_path}",
                f"static/{project.music_path}",
                project.idea,
                {'filename': f"static/{project.voice_path}", 'script': ''}
            )
            project.status = 'completed'
            result = {'status': 'completed', 'message': 'Final video created successfully'}
        else:
            return jsonify({'error': 'Invalid step'}), 400

        db.session.commit()

        return jsonify({
            'status': result.get('status', 'completed'),
            'message': result.get('message', f'Project {step} generation completed'),
        })
    except Exception as e:
        project.status = 'error'
        db.session.commit()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/project/<int:project_id>/status', methods=['GET'])
@login_required
def project_status(project_id):
    project = Project.query.get_or_404(project_id)

    # Check if the project belongs to the current user
    if project.user_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403

    # Get task ID from query parameter
    task_id = request.args.get('task_id')

    if task_id:
        # Get task status from Celery
        from celery.result import AsyncResult
        task_result = AsyncResult(task_id)

        if task_result.state == 'PENDING':
            response = {
                'status': 'pending',
                'message': 'Task is pending'
            }
        elif task_result.state == 'PROGRESS':
            response = {
                'status': 'processing',
                'message': task_result.info.get('message', 'Processing...'),
                'progress': task_result.info.get('progress', 0),
                'step': task_result.info.get('step', '')
            }
        elif task_result.state == 'SUCCESS':
            response = task_result.result
        else:
            response = {
                'status': 'error',
                'message': str(task_result.result) if task_result.result else 'Unknown error'
            }
    else:
        # Return project status from database
        response = {
            'status': project.status,
            'message': f'Project is {project.status}'
        }

    return jsonify(response)

# Register API blueprint
from api import api_bp
app.register_blueprint(api_bp)

# Register analytics blueprint
from analytics.dashboard import analytics_bp
app.register_blueprint(analytics_bp)

# Register admin blueprint
from admin import admin_bp
app.register_blueprint(admin_bp)

# Register payments blueprint
from payments.routes import payments_bp
app.register_blueprint(payments_bp)

# Initialize analytics
from analytics import Analytics
analytics = Analytics(app)

# Initialize email
from notifications import mail
mail.init_app(app)

# Initialize storage
from storage import StorageManager
storage_manager = StorageManager(app)

# Theme setting route
@app.route('/set_theme', methods=['POST'])
def set_theme():
    """Set the theme preference (light or dark)."""
    data = request.json
    theme = data.get('theme', 'light')
    session['theme'] = theme
    return jsonify({'status': 'success', 'theme': theme})

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
