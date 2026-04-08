# Assumptions Made Due to Incomplete Requirements

## Part 1 — Debugging
1. `initial_quantity` is optional — defaults to 0 if not provided
2. Authentication is required on all endpoints
3. SKU uniqueness is enforced at the application layer before DB insert

## Part 2 — Database Design
4. SKUs are unique across the entire platform (not just per company)
5. Price is global per product, not per warehouse
6. Bundles cannot be nested (a bundle cannot contain another bundle)
7. Inventory quantity cannot go below zero
8. All timestamps stored in UTC

## Part 3 — Low Stock Alert API
9. "Recent sales activity" = at least 1 sale within the last 30 days
10. Low stock threshold is stored at the product level (not per warehouse)
11. days_until_stockout = current_stock ÷ avg daily sales over last 30 days
12. If avg daily sales = 0, days_until_stockout returns null (unpredictable)
13. Products with no supplier return supplier: null (not an error)
14. Alerts are sorted by urgency — lowest days_until_stockout first

## Questions I Would Ask the Product Team
- What defines "recent" sales — 7 days? 30 days?
- Should threshold be per-product or per-warehouse?
- Can bundles be nested inside other bundles?
- Is pricing per warehouse or global?
- Do we need soft-delete for products?
- Multi-currency support required?
- What user roles exist — who can create products / view alerts?