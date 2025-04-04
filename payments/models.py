from app import db
from datetime import datetime

class Subscription(db.Model):
    """Model for user subscriptions."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stripe_customer_id = db.Column(db.String(100), nullable=True)
    stripe_subscription_id = db.Column(db.String(100), nullable=True)
    plan = db.Column(db.String(20), nullable=False, default='free')
    status = db.Column(db.String(20), nullable=False, default='active')
    current_period_start = db.Column(db.DateTime, nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('subscription', uselist=False))
    
    def __repr__(self):
        return f'<Subscription {self.plan}>'

class Invoice(db.Model):
    """Model for subscription invoices."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stripe_invoice_id = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # Amount in cents
    currency = db.Column(db.String(3), nullable=False, default='usd')
    status = db.Column(db.String(20), nullable=False)
    invoice_pdf = db.Column(db.String(255), nullable=True)
    invoice_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('invoices', lazy=True))
    
    def __repr__(self):
        return f'<Invoice {self.stripe_invoice_id}>'

class PaymentMethod(db.Model):
    """Model for user payment methods."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stripe_payment_method_id = db.Column(db.String(100), nullable=False)
    card_brand = db.Column(db.String(20), nullable=False)
    card_last4 = db.Column(db.String(4), nullable=False)
    card_exp_month = db.Column(db.Integer, nullable=False)
    card_exp_year = db.Column(db.Integer, nullable=False)
    is_default = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('payment_methods', lazy=True))
    
    def __repr__(self):
        return f'<PaymentMethod {self.card_brand} **** **** **** {self.card_last4}>'
