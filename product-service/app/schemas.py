def validate_product(data):
    """Validate product data"""
    errors = []

    if not data.get('name'):
        errors.append('Name is required')
    elif len(data.get('name', '')) < 3:
        errors.append('Name must be at least 3 characters')

    if 'price' not in data:
        errors.append('Price is required')
    elif not isinstance(data.get('price'), (int, float)) or data.get('price') < 0:
        errors.append('Price must be a positive number')

    if 'stock' in data:
        if not isinstance(data.get('stock'), int) or data.get('stock') < 0:
            errors.append('Stock must be a non-negative integer')

    return errors
