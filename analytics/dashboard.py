from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from app import db, User, Project
from .models import UserActivity, ProjectMetrics, ApiUsage, ErrorLog

# Create a Blueprint for the analytics dashboard
analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/')
@login_required
def dashboard():
    """Analytics dashboard main page."""
    # Check if user is admin
    if current_user.subscription_tier != 'admin':
        return render_template('analytics/access_denied.html')
    
    # Get basic stats
    user_count = User.query.count()
    project_count = Project.query.count()
    completed_projects = Project.query.filter_by(status='completed').count()
    error_count = ErrorLog.query.count()
    
    # Get user registration trend
    user_trend = get_user_registration_trend()
    
    # Get project creation trend
    project_trend = get_project_creation_trend()
    
    # Get subscription tier distribution
    subscription_distribution = get_subscription_distribution()
    
    # Get average generation times
    generation_times = get_average_generation_times()
    
    return render_template(
        'analytics/dashboard.html',
        user_count=user_count,
        project_count=project_count,
        completed_projects=completed_projects,
        error_count=error_count,
        user_trend=user_trend,
        project_trend=project_trend,
        subscription_distribution=subscription_distribution,
        generation_times=generation_times
    )

@analytics_bp.route('/users')
@login_required
def user_analytics():
    """User analytics page."""
    # Check if user is admin
    if current_user.subscription_tier != 'admin':
        return render_template('analytics/access_denied.html')
    
    # Get most active users
    active_users = db.session.query(
        User, func.count(UserActivity.id).label('activity_count')
    ).join(UserActivity).group_by(User.id).order_by(desc('activity_count')).limit(10).all()
    
    # Get users with most projects
    users_with_projects = db.session.query(
        User, func.count(Project.id).label('project_count')
    ).join(Project).group_by(User.id).order_by(desc('project_count')).limit(10).all()
    
    # Get new users in the last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    new_users = User.query.filter(User.created_at >= thirty_days_ago).count()
    
    # Get subscription tier changes
    # This would require a subscription history table, which we haven't implemented yet
    
    return render_template(
        'analytics/users.html',
        active_users=active_users,
        users_with_projects=users_with_projects,
        new_users=new_users
    )

@analytics_bp.route('/projects')
@login_required
def project_analytics():
    """Project analytics page."""
    # Check if user is admin
    if current_user.subscription_tier != 'admin':
        return render_template('analytics/access_denied.html')
    
    # Get projects by status
    projects_by_status = db.session.query(
        Project.status, func.count(Project.id).label('count')
    ).group_by(Project.status).all()
    
    # Get average generation time by step
    avg_generation_times = db.session.query(
        func.avg(ProjectMetrics.image_generation_time).label('avg_image_time'),
        func.avg(ProjectMetrics.video_generation_time).label('avg_video_time'),
        func.avg(ProjectMetrics.music_generation_time).label('avg_music_time'),
        func.avg(ProjectMetrics.voice_generation_time).label('avg_voice_time'),
        func.avg(ProjectMetrics.final_video_time).label('avg_final_time')
    ).first()
    
    # Get projects created in the last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_projects = Project.query.filter(Project.created_at >= thirty_days_ago).count()
    
    return render_template(
        'analytics/projects.html',
        projects_by_status=projects_by_status,
        avg_generation_times=avg_generation_times,
        recent_projects=recent_projects
    )

@analytics_bp.route('/errors')
@login_required
def error_analytics():
    """Error analytics page."""
    # Check if user is admin
    if current_user.subscription_tier != 'admin':
        return render_template('analytics/access_denied.html')
    
    # Get most common errors
    common_errors = db.session.query(
        ErrorLog.error_type, func.count(ErrorLog.id).label('count')
    ).group_by(ErrorLog.error_type).order_by(desc('count')).limit(10).all()
    
    # Get recent errors
    recent_errors = ErrorLog.query.order_by(ErrorLog.created_at.desc()).limit(20).all()
    
    return render_template(
        'analytics/errors.html',
        common_errors=common_errors,
        recent_errors=recent_errors
    )

@analytics_bp.route('/api')
@login_required
def api_analytics():
    """API usage analytics page."""
    # Check if user is admin
    if current_user.subscription_tier != 'admin':
        return render_template('analytics/access_denied.html')
    
    # Get most used endpoints
    popular_endpoints = db.session.query(
        ApiUsage.endpoint, func.count(ApiUsage.id).label('count')
    ).group_by(ApiUsage.endpoint).order_by(desc('count')).limit(10).all()
    
    # Get average response time by endpoint
    response_times = db.session.query(
        ApiUsage.endpoint, func.avg(ApiUsage.response_time).label('avg_time')
    ).group_by(ApiUsage.endpoint).order_by(desc('avg_time')).limit(10).all()
    
    # Get API usage by user
    api_usage_by_user = db.session.query(
        User, func.count(ApiUsage.id).label('count')
    ).join(ApiUsage).group_by(User.id).order_by(desc('count')).limit(10).all()
    
    return render_template(
        'analytics/api.html',
        popular_endpoints=popular_endpoints,
        response_times=response_times,
        api_usage_by_user=api_usage_by_user
    )

# Helper functions for analytics data

def get_user_registration_trend():
    """Get user registration trend for the last 30 days."""
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    # Query users created in the last 30 days, grouped by day
    result = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(User.created_at >= thirty_days_ago).group_by('date').all()
    
    # Convert to dictionary with date strings as keys
    trend = {str(row.date): row.count for row in result}
    
    # Fill in missing dates with zero counts
    for i in range(30):
        date = (datetime.now() - timedelta(days=i)).date()
        if str(date) not in trend:
            trend[str(date)] = 0
    
    return trend

def get_project_creation_trend():
    """Get project creation trend for the last 30 days."""
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    # Query projects created in the last 30 days, grouped by day
    result = db.session.query(
        func.date(Project.created_at).label('date'),
        func.count(Project.id).label('count')
    ).filter(Project.created_at >= thirty_days_ago).group_by('date').all()
    
    # Convert to dictionary with date strings as keys
    trend = {str(row.date): row.count for row in result}
    
    # Fill in missing dates with zero counts
    for i in range(30):
        date = (datetime.now() - timedelta(days=i)).date()
        if str(date) not in trend:
            trend[str(date)] = 0
    
    return trend

def get_subscription_distribution():
    """Get distribution of users by subscription tier."""
    result = db.session.query(
        User.subscription_tier,
        func.count(User.id).label('count')
    ).group_by(User.subscription_tier).all()
    
    # Convert to dictionary
    distribution = {row.subscription_tier: row.count for row in result}
    
    return distribution

def get_average_generation_times():
    """Get average generation times for each step."""
    result = db.session.query(
        func.avg(ProjectMetrics.image_generation_time).label('image'),
        func.avg(ProjectMetrics.video_generation_time).label('video'),
        func.avg(ProjectMetrics.music_generation_time).label('music'),
        func.avg(ProjectMetrics.voice_generation_time).label('voice'),
        func.avg(ProjectMetrics.final_video_time).label('final')
    ).first()
    
    # Convert to dictionary
    times = {
        'image': result.image or 0,
        'video': result.video or 0,
        'music': result.music or 0,
        'voice': result.voice or 0,
        'final': result.final or 0
    }
    
    return times
