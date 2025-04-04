from flask import request, g
from datetime import datetime
import json
import os
from app import db

class Analytics:
    """Analytics module for tracking user activity."""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the analytics module with the Flask app."""
        self.app = app
        
        # Create analytics directory if it doesn't exist
        os.makedirs('analytics/logs', exist_ok=True)
        
        # Register before_request handler
        app.before_request(self.before_request)
        
        # Register after_request handler
        app.after_request(self.after_request)
    
    def before_request(self):
        """Store request start time."""
        g.start_time = datetime.now()
    
    def after_request(self, response):
        """Log request details."""
        if hasattr(g, 'start_time'):
            # Calculate request duration
            duration = (datetime.now() - g.start_time).total_seconds()
            
            # Get user ID if authenticated
            user_id = None
            if hasattr(g, 'user') and g.user:
                user_id = g.user.id
            
            # Log request details
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration': duration,
                'user_id': user_id,
                'ip': request.remote_addr,
                'user_agent': request.user_agent.string
            }
            
            # Write to log file
            self.write_log(log_data)
        
        return response
    
    def write_log(self, log_data):
        """Write log data to file."""
        log_file = f"analytics/logs/{datetime.now().strftime('%Y-%m-%d')}.log"
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_data) + '\n')
    
    def track_event(self, event_type, event_data=None, user_id=None):
        """Track a custom event."""
        if event_data is None:
            event_data = {}
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'event_data': event_data,
            'user_id': user_id,
            'ip': request.remote_addr if request else None,
            'user_agent': request.user_agent.string if request and request.user_agent else None
        }
        
        # Write to log file
        self.write_log(log_data)
        
        return log_data
