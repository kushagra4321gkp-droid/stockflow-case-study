from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError

@app.route('/api/products', methods=['POST'])
@login_required  # FIX 1: Added authentication - original had no auth
def create_product():
    data = request.json

    # FIX 2: Validate all required fields exist
    # Original code would crash with KeyError if any field was missing
    required_fields = ['name', 'sku', 'price', 'warehouse_id']
    for field in required_fields:
        if not data or field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # FIX 3: Validate price is a positive decimal
    # Original accepted negative/zero/string prices without complaint
    try:
        price = float(data['price'])
        if price <= 0:
            return jsonify({"error": "Price must be a positive number"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid price format"}), 400

    # FIX 4: Enforce SKU uniqueness before inserting
    # Original had no check - duplicate SKUs would corrupt data
    if Product.query.filter_by(sku=data['sku']).first():
        return jsonify({"error": "A product with this SKU already exists"}), 409

    # FIX 5: Default initial_quantity to 0 if not provided
    # Original would crash with KeyError if initial_quantity was missing
    initial_quantity = data.get('initial_quantity', 0)

    try:
        # FIX 6: Use a single atomic transaction
        # Original had TWO separate commits — if the second failed,
        # a product would exist in DB with no inventory record (orphaned data)
        product = Product(
            name=data['name'],
            sku=data['sku'],
            price=price,
            warehouse_id=data['warehouse_id']
        )
        db.session.add(product)
        db.session.flush()  # Get product.id without committing yet

        inventory = Inventory(
            product_id=product.id,
            warehouse_id=data['warehouse_id'],
            quantity=initial_quantity
        )
        db.session.add(inventory)
        db.session.commit()  # Single commit — both succeed or both fail

        # FIX 7: Return 201 Created instead of default 200
        # REST convention: resource creation = 201
        return jsonify({
            "message": "Product created",
            "product_id": product.id
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()  # Roll back everything on failure
        return jsonify({"error": "Database error", "details": str(e)}), 500