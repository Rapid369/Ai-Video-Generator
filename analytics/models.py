from app import db
from datetime import datetime

class UserActivity(db.Model):
    """Model for tracking user activity."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    activity_type = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('activities', lazy=True))
    
    def __repr__(self):
        return f'<UserActivity {self.activity_type}>'

class ProjectMetrics(db.Model):
    """Model for tracking project metrics."""
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    generation_time = db.Column(db.Float, nullable=True)  # Time in seconds
    idea_tokens = db.Column(db.Integer, nullable=True)
    prompt_tokens = db.Column(db.Integer, nullable=True)
    image_generation_time = db.Column(db.Float, nullable=True)
    video_generation_time = db.Column(db.Float, nullable=True)
    music_generation_time = db.Column(db.Float, nullable=True)
    voice_generation_time = db.Column(db.Float, nullable=True)
    final_video_time = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    project = db.relationship('Project', backref=db.backref('metrics', lazy=True))
    
    def __repr__(self):
        return f'<ProjectMetrics {self.project_id}>'

class ApiUsage(db.Model):
    """Model for tracking API usage."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    endpoint = db.Column(db.String(100), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    response_time = db.Column(db.Float, nullable=False)  # Time in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('api_usage', lazy=True))
    
    def __repr__(self):
        return f'<ApiUsage {self.endpoint}>'

class ErrorLog(db.Model):
    """Model for tracking errors."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    error_type = db.Column(db.String(100), nullable=False)
    error_message = db.Column(db.Text, nullable=False)
    stack_trace = db.Column(db.Text, nullable=True)
    url = db.Column(db.String(255), nullable=True)
    method = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('errors', lazy=True))
    
    def __repr__(self):
        return f'<ErrorLog {self.error_type}>'
