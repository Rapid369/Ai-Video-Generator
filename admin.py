from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db, User, Project
from analytics.models import UserActivity, ProjectMetrics, ApiUsage, ErrorLog
from sqlalchemy import desc

# Create a Blueprint for the admin panel
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
def check_admin():
    """Check if the user is an admin before processing any request."""
    if not current_user.is_authenticated or current_user.subscription_tier != 'admin':
        return render_template('admin/access_denied.html')

@admin_bp.route('/')
@login_required
def dashboard():
    """Admin dashboard main page."""
    # Get basic stats
    user_count = User.query.count()
    project_count = Project.query.count()
    completed_projects = Project.query.filter_by(status='completed').count()
    error_count = ErrorLog.query.count()
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Get recent projects
    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()
    
    # Get recent errors
    recent_errors = ErrorLog.query.order_by(ErrorLog.created_at.desc()).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        user_count=user_count,
        project_count=project_count,
        completed_projects=completed_projects,
        error_count=error_count,
        recent_users=recent_users,
        recent_projects=recent_projects,
        recent_errors=recent_errors
    )

@admin_bp.route('/users')
@login_required
def users():
    """User management page."""
    # Get all users
    users = User.query.order_by(User.created_at.desc()).all()
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>')
@login_required
def user_detail(user_id):
    """User detail page."""
    # Get user
    user = User.query.get_or_404(user_id)
    
    # Get user's projects
    projects = Project.query.filter_by(user_id=user_id).order_by(Project.created_at.desc()).all()
    
    # Get user's activities
    activities = UserActivity.query.filter_by(user_id=user_id).order_by(UserActivity.created_at.desc()).limit(20).all()
    
    return render_template(
        'admin/user_detail.html',
        user=user,
        projects=projects,
        activities=activities
    )

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(user_id):
    """User edit page."""
    # Get user
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Update user
        user.name = request.form.get('name')
        user.email = request.form.get('email')
        user.subscription_tier = request.form.get('subscription_tier')
        
        # Update API keys if provided
        if request.form.get('openai_api_key'):
            user.openai_api_key = request.form.get('openai_api_key')
        
        if request.form.get('replicate_api_key'):
            user.replicate_api_key = request.form.get('replicate_api_key')
        
        if request.form.get('sonauto_api_key'):
            user.sonauto_api_key = request.form.get('sonauto_api_key')
        
        # Save changes
        db.session.commit()
        
        flash('User updated successfully')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    return render_template('admin/user_edit.html', user=user)

@admin_bp.route('/projects')
@login_required
def projects():
    """Project management page."""
    # Get all projects
    projects = Project.query.order_by(Project.created_at.desc()).all()
    
    return render_template('admin/projects.html', projects=projects)

@admin_bp.route('/projects/<int:project_id>')
@login_required
def project_detail(project_id):
    """Project detail page."""
    # Get project
    project = Project.query.get_or_404(project_id)
    
    # Get project metrics
    metrics = ProjectMetrics.query.filter_by(project_id=project_id).first()
    
    return render_template(
        'admin/project_detail.html',
        project=project,
        metrics=metrics
    )

@admin_bp.route('/errors')
@login_required
def errors():
    """Error management page."""
    # Get all errors
    errors = ErrorLog.query.order_by(ErrorLog.created_at.desc()).all()
    
    return render_template('admin/errors.html', errors=errors)

@admin_bp.route('/settings')
@login_required
def settings():
    """Admin settings page."""
    return render_template('admin/settings.html')
