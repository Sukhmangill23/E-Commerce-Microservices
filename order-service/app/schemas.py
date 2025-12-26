def validate_order(data):
    """Validate order data"""
    errors = []

    if 'user_id' not in data:
        errors.append('User ID is required')
    else:
        # Convert string to int if needed (JWT returns string)
        try:
            user_id = int(data.get('user_id'))
            data['user_id'] = user_id  # Update with integer value
        except (ValueError, TypeError):
            errors.append('User ID must be a valid integer')

    if 'products' not in data:
        errors.append('Products are required')
    elif not isinstance(data.get('products'), list) or len(data.get('products', [])) == 0:
        errors.append('Products must be a non-empty list')
    else:
        for idx, product in enumerate(data['products']):
            if 'product_id' not in product:
                errors.append(f'Product {idx}: product_id is required')
            if 'quantity' not in product:
                errors.append(f'Product {idx}: quantity is required')
            elif not isinstance(product.get('quantity'), int) or product.get('quantity') <= 0:
                errors.append(f'Product {idx}: quantity must be a positive integer')

    return errors
