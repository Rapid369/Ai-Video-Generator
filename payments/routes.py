from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
import stripe
from app import db
from .models import Subscription, Invoice, PaymentMethod
from . import SUBSCRIPTION_PLANS
import json
from datetime import datetime

# Create a Blueprint for the payments
payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

@payments_bp.route('/pricing')
def pricing():
    """Display pricing plans."""
    return render_template('payments/pricing.html', plans=SUBSCRIPTION_PLANS)

@payments_bp.route('/checkout/<plan>')
@login_required
def checkout(plan):
    """Checkout page for a subscription plan."""
    if plan not in SUBSCRIPTION_PLANS:
        flash('Invalid subscription plan')
        return redirect(url_for('payments.pricing'))
    
    # Free plan doesn't need checkout
    if plan == 'free':
        # Update user's subscription tier
        current_user.subscription_tier = 'free'
        
        # Create or update subscription record
        subscription = Subscription.query.filter_by(user_id=current_user.id).first()
        if subscription:
            subscription.plan = 'free'
            subscription.status = 'active'
        else:
            subscription = Subscription(
                user_id=current_user.id,
                plan='free',
                status='active'
            )
            db.session.add(subscription)
        
        db.session.commit()
        
        flash('You have successfully subscribed to the Free plan')
        return redirect(url_for('dashboard'))
    
    # Get the selected plan
    selected_plan = SUBSCRIPTION_PLANS[plan]
    
    return render_template(
        'payments/checkout.html',
        plan=plan,
        plan_details=selected_plan
    )

@payments_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create a Stripe checkout session."""
    plan = request.form.get('plan')
    
    if plan not in SUBSCRIPTION_PLANS or plan == 'free':
        return jsonify({'error': 'Invalid plan'}), 400
    
    # Get the price ID for the selected plan
    price_id = SUBSCRIPTION_PLANS[plan].get('stripe_price_id')
    
    if not price_id:
        return jsonify({'error': 'Price ID not configured for this plan'}), 400
    
    # Check if user already has a Stripe customer ID
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    customer_id = None
    
    if subscription and subscription.stripe_customer_id:
        customer_id = subscription.stripe_customer_id
    else:
        # Create a new customer in Stripe
        customer = stripe.Customer.create(
            email=current_user.email,
            name=current_user.name,
            metadata={
                'user_id': current_user.id
            }
        )
        customer_id = customer.id
        
        # Create or update subscription record
        if subscription:
            subscription.stripe_customer_id = customer_id
        else:
            subscription = Subscription(
                user_id=current_user.id,
                stripe_customer_id=customer_id,
                plan=plan,
                status='incomplete'
            )
            db.session.add(subscription)
        
        db.session.commit()
    
    # Create a checkout session
    try:
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=request.host_url + url_for('payments.success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + url_for('payments.cancel'),
            metadata={
                'user_id': current_user.id,
                'plan': plan
            }
        )
        
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@payments_bp.route('/success')
@login_required
def success():
    """Handle successful checkout."""
    session_id = request.args.get('session_id')
    
    if not session_id:
        flash('Invalid session')
        return redirect(url_for('payments.pricing'))
    
    try:
        # Retrieve the checkout session
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Get the subscription ID
        subscription_id = checkout_session.subscription
        
        # Retrieve the subscription
        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Update user's subscription
        subscription = Subscription.query.filter_by(user_id=current_user.id).first()
        
        if subscription:
            subscription.stripe_subscription_id = subscription_id
            subscription.plan = checkout_session.metadata.get('plan')
            subscription.status = stripe_subscription.status
            subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
            subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
        else:
            subscription = Subscription(
                user_id=current_user.id,
                stripe_customer_id=checkout_session.customer,
                stripe_subscription_id=subscription_id,
                plan=checkout_session.metadata.get('plan'),
                status=stripe_subscription.status,
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end)
            )
            db.session.add(subscription)
        
        # Update user's subscription tier
        current_user.subscription_tier = checkout_session.metadata.get('plan')
        
        db.session.commit()
        
        flash('Thank you for your subscription!')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'Error processing subscription: {str(e)}')
        return redirect(url_for('payments.pricing'))

@payments_bp.route('/cancel')
@login_required
def cancel():
    """Handle cancelled checkout."""
    flash('Subscription checkout was cancelled')
    return redirect(url_for('payments.pricing'))

@payments_bp.route('/billing')
@login_required
def billing():
    """Display billing information."""
    # Get user's subscription
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    
    # Get user's payment methods
    payment_methods = PaymentMethod.query.filter_by(user_id=current_user.id).all()
    
    # Get user's invoices
    invoices = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.invoice_date.desc()).all()
    
    return render_template(
        'payments/billing.html',
        subscription=subscription,
        payment_methods=payment_methods,
        invoices=invoices,
        plans=SUBSCRIPTION_PLANS
    )

@payments_bp.route('/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel a subscription."""
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    
    if not subscription or not subscription.stripe_subscription_id:
        flash('No active subscription found')
        return redirect(url_for('payments.billing'))
    
    try:
        # Cancel the subscription at the end of the billing period
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True
        )
        
        # Update subscription record
        subscription.cancel_at_period_end = True
        db.session.commit()
        
        flash('Your subscription will be cancelled at the end of the billing period')
    except Exception as e:
        flash(f'Error cancelling subscription: {str(e)}')
    
    return redirect(url_for('payments.billing'))

@payments_bp.route('/reactivate-subscription', methods=['POST'])
@login_required
def reactivate_subscription():
    """Reactivate a cancelled subscription."""
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    
    if not subscription or not subscription.stripe_subscription_id:
        flash('No subscription found')
        return redirect(url_for('payments.billing'))
    
    try:
        # Reactivate the subscription
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=False
        )
        
        # Update subscription record
        subscription.cancel_at_period_end = False
        db.session.commit()
        
        flash('Your subscription has been reactivated')
    except Exception as e:
        flash(f'Error reactivating subscription: {str(e)}')
    
    return redirect(url_for('payments.billing'))

@payments_bp.route('/change-plan', methods=['POST'])
@login_required
def change_plan():
    """Change subscription plan."""
    new_plan = request.form.get('plan')
    
    if new_plan not in SUBSCRIPTION_PLANS:
        flash('Invalid subscription plan')
        return redirect(url_for('payments.billing'))
    
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    
    if not subscription or not subscription.stripe_subscription_id:
        # If no subscription exists, redirect to checkout
        return redirect(url_for('payments.checkout', plan=new_plan))
    
    # Free plan doesn't need Stripe
    if new_plan == 'free':
        try:
            # Cancel the current subscription
            stripe.Subscription.delete(subscription.stripe_subscription_id)
            
            # Update subscription record
            subscription.plan = 'free'
            subscription.status = 'active'
            subscription.stripe_subscription_id = None
            
            # Update user's subscription tier
            current_user.subscription_tier = 'free'
            
            db.session.commit()
            
            flash('Your subscription has been downgraded to the Free plan')
        except Exception as e:
            flash(f'Error changing subscription: {str(e)}')
        
        return redirect(url_for('payments.billing'))
    
    # Get the price ID for the new plan
    price_id = SUBSCRIPTION_PLANS[new_plan].get('stripe_price_id')
    
    if not price_id:
        flash('Price ID not configured for this plan')
        return redirect(url_for('payments.billing'))
    
    try:
        # Update the subscription
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            items=[{
                'id': stripe.Subscription.retrieve(subscription.stripe_subscription_id)['items']['data'][0].id,
                'price': price_id,
            }],
            proration_behavior='create_prorations'
        )
        
        # Update subscription record
        subscription.plan = new_plan
        
        # Update user's subscription tier
        current_user.subscription_tier = new_plan
        
        db.session.commit()
        
        flash(f'Your subscription has been updated to the {SUBSCRIPTION_PLANS[new_plan]["name"]} plan')
    except Exception as e:
        flash(f'Error changing subscription: {str(e)}')
    
    return redirect(url_for('payments.billing'))

@payments_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events."""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, current_app.config['STRIPE_WEBHOOK_SECRET']
        )
    except ValueError as e:
        # Invalid payload
        return jsonify({'error': str(e)}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify({'error': str(e)}), 400
    
    # Handle the event
    if event['type'] == 'customer.subscription.updated':
        handle_subscription_updated(event['data']['object'])
    elif event['type'] == 'customer.subscription.deleted':
        handle_subscription_deleted(event['data']['object'])
    elif event['type'] == 'invoice.payment_succeeded':
        handle_invoice_payment_succeeded(event['data']['object'])
    elif event['type'] == 'invoice.payment_failed':
        handle_invoice_payment_failed(event['data']['object'])
    
    return jsonify({'status': 'success'})

def handle_subscription_updated(subscription_object):
    """Handle subscription updated event."""
    subscription_id = subscription_object['id']
    
    # Find the subscription in our database
    subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_id).first()
    
    if subscription:
        # Update subscription status
        subscription.status = subscription_object['status']
        subscription.current_period_start = datetime.fromtimestamp(subscription_object['current_period_start'])
        subscription.current_period_end = datetime.fromtimestamp(subscription_object['current_period_end'])
        subscription.cancel_at_period_end = subscription_object['cancel_at_period_end']
        
        db.session.commit()

def handle_subscription_deleted(subscription_object):
    """Handle subscription deleted event."""
    subscription_id = subscription_object['id']
    
    # Find the subscription in our database
    subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_id).first()
    
    if subscription:
        # Update subscription status
        subscription.status = 'cancelled'
        subscription.stripe_subscription_id = None
        
        # Update user's subscription tier to free
        user = subscription.user
        if user:
            user.subscription_tier = 'free'
        
        db.session.commit()

def handle_invoice_payment_succeeded(invoice_object):
    """Handle invoice payment succeeded event."""
    # Check if this is a subscription invoice
    if not invoice_object.get('subscription'):
        return
    
    # Find the customer in our database
    subscription = Subscription.query.filter_by(stripe_customer_id=invoice_object['customer']).first()
    
    if subscription:
        # Create an invoice record
        invoice = Invoice(
            user_id=subscription.user_id,
            stripe_invoice_id=invoice_object['id'],
            amount=invoice_object['amount_paid'],
            currency=invoice_object['currency'],
            status=invoice_object['status'],
            invoice_pdf=invoice_object.get('invoice_pdf'),
            invoice_date=datetime.fromtimestamp(invoice_object['created'])
        )
        
        db.session.add(invoice)
        db.session.commit()

def handle_invoice_payment_failed(invoice_object):
    """Handle invoice payment failed event."""
    # Check if this is a subscription invoice
    if not invoice_object.get('subscription'):
        return
    
    # Find the subscription in our database
    subscription = Subscription.query.filter_by(stripe_subscription_id=invoice_object['subscription']).first()
    
    if subscription:
        # Update subscription status
        subscription.status = 'past_due'
        
        db.session.commit()
