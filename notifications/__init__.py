from flask_mail import Mail, Message
from flask import current_app, render_template
from threading import Thread

# Initialize Flask-Mail
mail = Mail()

def send_async_email(app, msg):
    """Send email asynchronously."""
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, template, **kwargs):
    """Send an email using a template."""
    app = current_app._get_current_object()
    msg = Message(subject, recipients=recipients)
    msg.html = render_template(template, **kwargs)
    
    # Send email asynchronously
    Thread(target=send_async_email, args=(app, msg)).start()

def send_welcome_email(user):
    """Send a welcome email to a new user."""
    send_email(
        subject="Welcome to AI Video Generator!",
        recipients=[user.email],
        template="emails/welcome.html",
        user=user
    )

def send_password_reset_email(user, token):
    """Send a password reset email to a user."""
    send_email(
        subject="Reset Your Password",
        recipients=[user.email],
        template="emails/password_reset.html",
        user=user,
        token=token
    )

def send_subscription_confirmation_email(user, subscription):
    """Send a subscription confirmation email to a user."""
    from payments import SUBSCRIPTION_PLANS
    
    plan_details = SUBSCRIPTION_PLANS.get(subscription.plan, {})
    
    send_email(
        subject="Subscription Confirmation",
        recipients=[user.email],
        template="emails/subscription_confirmation.html",
        user=user,
        subscription=subscription,
        plan_details=plan_details
    )

def send_subscription_cancelled_email(user, subscription):
    """Send a subscription cancellation email to a user."""
    from payments import SUBSCRIPTION_PLANS
    
    plan_details = SUBSCRIPTION_PLANS.get(subscription.plan, {})
    
    send_email(
        subject="Subscription Cancelled",
        recipients=[user.email],
        template="emails/subscription_cancelled.html",
        user=user,
        subscription=subscription,
        plan_details=plan_details
    )

def send_project_completed_email(user, project):
    """Send a project completion email to a user."""
    send_email(
        subject="Your Video is Ready!",
        recipients=[user.email],
        template="emails/project_completed.html",
        user=user,
        project=project
    )

def send_payment_failed_email(user, subscription):
    """Send a payment failed email to a user."""
    send_email(
        subject="Payment Failed",
        recipients=[user.email],
        template="emails/payment_failed.html",
        user=user,
        subscription=subscription
    )
