from flask import Flask
from models import db

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/stockflow'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Register routes
    from low_stock_alert import low_stock_alerts
    from fixed_code import create_product
    app.add_url_rule(
        '/api/companies/<int:company_id>/alerts/low-stock',
        view_func=low_stock_alerts
    )
    app.add_url_rule(
        '/api/products',
        view_func=create_product,
        methods=['POST']
    )

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)