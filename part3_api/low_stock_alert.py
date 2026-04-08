from flask import jsonify
from sqlalchemy import func
from datetime import datetime, timedelta
from models import db, Company, Product, Inventory, Warehouse, Supplier, Sale

# Assumption: "recent sales activity" = at least 1 sale in last 30 days
RECENT_SALES_DAYS = 30

@app.route('/api/companies/<int:company_id>/alerts/low-stock', methods=['GET'])
@login_required
def low_stock_alerts(company_id):

    # Validate company exists
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"error": "Company not found"}), 404

    since_date = datetime.utcnow() - timedelta(days=RECENT_SALES_DAYS)

    # Query: products that are low on stock AND have recent sales activity
    # Joins: inventory → product → warehouse → supplier + recent sales
    results = (
        db.session.query(
            Product,
            Inventory,
            Warehouse,
            Supplier,
            func.sum(Sale.quantity_sold).label('total_sold')
        )
        .join(Inventory, Inventory.product_id == Product.id)
        .join(Warehouse, Warehouse.id == Inventory.warehouse_id)
        .outerjoin(Supplier, Supplier.id == Product.supplier_id)
        # Inner join on sales — excludes products with no recent sales
        .join(
            Sale,
            (Sale.product_id == Product.id) &
            (Sale.warehouse_id == Inventory.warehouse_id) &
            (Sale.sold_at >= since_date)
        )
        .filter(
            Warehouse.company_id == company_id,
            Product.is_active == True,
            # Low stock condition
            Inventory.quantity <= Product.low_stock_threshold
        )
        .group_by(Product.id, Inventory.id, Warehouse.id, Supplier.id)
        .all()
    )

    alerts = []
    for product, inventory, warehouse, supplier, total_sold in results:

        # Calculate days until stockout based on avg daily sales velocity
        # If avg_daily_sales is 0, we can't predict — return None
        avg_daily_sales = total_sold / RECENT_SALES_DAYS
        days_until_stockout = (
            round(inventory.quantity / avg_daily_sales)
            if avg_daily_sales > 0
            else None
        )

        alerts.append({
            "product_id":         product.id,
            "product_name":       product.name,
            "sku":                product.sku,
            "warehouse_id":       warehouse.id,
            "warehouse_name":     warehouse.name,
            "current_stock":      inventory.quantity,
            "threshold":          product.low_stock_threshold,
            "days_until_stockout": days_until_stockout,
            "supplier": {
                "id":            supplier.id,
                "name":          supplier.name,
                "contact_email": supplier.contact_email
            } if supplier else None
        })

    # Sort by most urgent first (None = unknown = least urgent)
    alerts.sort(key=lambda x: x["days_until_stockout"] or float('inf'))

    return jsonify({
        "alerts":       alerts,
        "total_alerts": len(alerts)
    }), 200