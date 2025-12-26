from flask import jsonify


def validate_user_registration(data):
    """Validate user registration data"""
    errors = []

    if not data.get('username'):
        errors.append('Username is required')
    elif len(data.get('username', '')) < 3:
        errors.append('Username must be at least 3 characters')

    if not data.get('email'):
        errors.append('Email is required')
    elif '@' not in data.get('email', ''):
        errors.append('Invalid email format')

    if not data.get('password'):
        errors.append('Password is required')
    elif len(data.get('password', '')) < 6:
        errors.append('Password must be at least 6 characters')

    return errors


def validate_user_login(data):
    """Validate user login data"""
    errors = []

    if not data.get('username') and not data.get('email'):
        errors.append('Username or email is required')

    if not data.get('password'):
        errors.append('Password is required')

    return errors
