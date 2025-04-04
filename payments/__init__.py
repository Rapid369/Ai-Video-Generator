import os
import stripe
from flask import current_app

# Initialize Stripe with API key
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Set Stripe API version
stripe.api_version = '2023-10-16'

# Define subscription plans
SUBSCRIPTION_PLANS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'features': {
            'videos_per_month': 3,
            'resolution': '720p',
            'max_duration': 15,
            'support': 'Basic'
        }
    },
    'pro': {
        'name': 'Pro',
        'price': 29,
        'stripe_price_id': os.getenv('STRIPE_PRO_PRICE_ID'),
        'features': {
            'videos_per_month': 20,
            'resolution': '1080p',
            'max_duration': 30,
            'support': 'Priority'
        }
    },
    'enterprise': {
        'name': 'Enterprise',
        'price': 99,
        'stripe_price_id': os.getenv('STRIPE_ENTERPRISE_PRICE_ID'),
        'features': {
            'videos_per_month': 'Unlimited',
            'resolution': '4K',
            'max_duration': 60,
            'support': '24/7 Dedicated'
        }
    }
}
