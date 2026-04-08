-- ============================================================
-- StockFlow Database Schema
-- Candidate: Kushagra Tiwari
-- ============================================================

-- Companies using the StockFlow platform
CREATE TABLE companies (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Warehouses belong to a company
CREATE TABLE warehouses (
    id          SERIAL PRIMARY KEY,
    company_id  INT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    location    VARCHAR(500),
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Suppliers provide products to companies
CREATE TABLE suppliers (
    id              SERIAL PRIMARY KEY,
    company_id      INT NOT NULL REFERENCES companies(id),
    name            VARCHAR(255) NOT NULL,
    contact_email   VARCHAR(255),
    contact_phone   VARCHAR(50),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Products on the platform
-- SKU is unique platform-wide (assumption)
CREATE TABLE products (
    id                  SERIAL PRIMARY KEY,
    company_id          INT NOT NULL REFERENCES companies(id),
    supplier_id         INT REFERENCES suppliers(id) ON DELETE SET NULL,
    name                VARCHAR(255) NOT NULL,
    sku                 VARCHAR(100) NOT NULL UNIQUE,
    price               DECIMAL(10, 2) NOT NULL CHECK (price > 0),
    product_type        VARCHAR(50) DEFAULT 'simple' CHECK (product_type IN ('simple', 'bundle')),
    low_stock_threshold INT NOT NULL DEFAULT 10,
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- Inventory tracks quantity of a product in a specific warehouse
-- One record per product-warehouse pair
CREATE TABLE inventory (
    id              SERIAL PRIMARY KEY,
    product_id      INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    warehouse_id    INT NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    quantity        INT NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    updated_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_id, warehouse_id)
);

-- Full history of every inventory change for auditing
CREATE TABLE inventory_logs (
    id              SERIAL PRIMARY KEY,
    inventory_id    INT NOT NULL REFERENCES inventory(id),
    change_qty      INT NOT NULL,       -- positive = stock in, negative = stock out
    reason          VARCHAR(255),       -- 'sale', 'restock', 'manual_adjustment'
    changed_by      INT,                -- user_id (auth system reference)
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Bundle items — which products make up a bundle
-- Assumption: bundles cannot be nested
CREATE TABLE bundle_items (
    id              SERIAL PRIMARY KEY,
    bundle_id       INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    component_id    INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity        INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
    UNIQUE(bundle_id, component_id),
    CHECK (bundle_id != component_id)   -- A product cannot bundle itself
);

-- Sales records — needed to calculate recent activity and sales velocity
CREATE TABLE sales (
    id              SERIAL PRIMARY KEY,
    product_id      INT NOT NULL REFERENCES products(id),
    warehouse_id    INT NOT NULL REFERENCES warehouses(id),
    quantity_sold   INT NOT NULL CHECK (quantity_sold > 0),
    sold_at         TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- Indexes for query performance
-- ============================================================

CREATE INDEX idx_products_company     ON products(company_id);
CREATE INDEX idx_products_sku         ON products(sku);
CREATE INDEX idx_inventory_product    ON inventory(product_id);
CREATE INDEX idx_inventory_warehouse  ON inventory(warehouse_id);
CREATE INDEX idx_sales_product_date   ON sales(product_id, sold_at);
CREATE INDEX idx_sales_warehouse      ON sales(warehouse_id);
CREATE INDEX idx_warehouses_company   ON warehouses(company_id);