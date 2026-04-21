"""
Inventory Analytics Dashboard - Flask Backend
Connects to MySQL and exposes REST endpoints consumed by the frontend.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ── Database Config ────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "database": os.getenv("DB_NAME",     "inventory_db"),
    "user":     os.getenv("DB_USER",     "root"),
    "password": os.getenv("DB_PASSWORD", "1475369"),
    "autocommit": True,
}


def get_db():
    """Return a fresh MySQL connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        logger.error("DB connection failed: %s", e)
        raise


def query(sql: str, params=None, fetchone=False):
    """Execute a SELECT and return rows as list-of-dicts."""
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        return cur.fetchone() if fetchone else cur.fetchall()
    finally:
        conn.close()


def execute(sql: str, params=None):
    """Execute an INSERT / UPDATE / DELETE and return lastrowid."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


# ── Health ─────────────────────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    try:
        query("SELECT 1")
        return jsonify({"status": "ok", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ── Dashboard KPIs ─────────────────────────────────────────────────────────────
@app.route("/api/dashboard/kpis")
def dashboard_kpis():
    total_products   = query("SELECT COUNT(*) AS cnt FROM products WHERE is_active=1", fetchone=True)["cnt"]
    total_categories = query("SELECT COUNT(*) AS cnt FROM categories", fetchone=True)["cnt"]
    low_stock        = query(
        "SELECT COUNT(*) AS cnt FROM products WHERE quantity_in_stock <= reorder_level AND is_active=1",
        fetchone=True
    )["cnt"]
    out_of_stock     = query(
        "SELECT COUNT(*) AS cnt FROM products WHERE quantity_in_stock = 0 AND is_active=1",
        fetchone=True
    )["cnt"]

    inventory_value  = query(
        "SELECT ROUND(SUM(quantity_in_stock * cost_price), 2) AS val FROM products WHERE is_active=1",
        fetchone=True
    )["val"] or 0

    retail_value     = query(
        "SELECT ROUND(SUM(quantity_in_stock * unit_price), 2) AS val FROM products WHERE is_active=1",
        fetchone=True
    )["val"] or 0

    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    sales_revenue   = query(
        """SELECT ROUND(ABS(SUM(quantity * unit_price)), 2) AS rev
           FROM stock_movements
           WHERE movement_type='sale' AND created_at >= %s""",
        (thirty_days_ago,), fetchone=True
    )["rev"] or 0

    return jsonify({
        "total_products":   total_products,
        "total_categories": total_categories,
        "low_stock":        low_stock,
        "out_of_stock":     out_of_stock,
        "inventory_value":  float(inventory_value),
        "retail_value":     float(retail_value),
        "sales_revenue_30d":float(sales_revenue),
        "potential_profit": float(retail_value) - float(inventory_value),
    })


# ── Category Breakdown ─────────────────────────────────────────────────────────
@app.route("/api/dashboard/category-breakdown")
def category_breakdown():
    rows = query("""
        SELECT c.name AS category,
               COUNT(p.id)                                      AS product_count,
               ROUND(SUM(p.quantity_in_stock * p.cost_price),2) AS inventory_value,
               ROUND(SUM(p.quantity_in_stock * p.unit_price),2) AS retail_value,
               SUM(p.quantity_in_stock)                         AS total_units
        FROM categories c
        LEFT JOIN products p ON p.category_id = c.id AND p.is_active = 1
        GROUP BY c.id, c.name
        ORDER BY inventory_value DESC
    """)
    return jsonify(rows)


# ── Stock Movements (last 30 days, daily) ─────────────────────────────────────
@app.route("/api/dashboard/stock-trend")
def stock_trend():
    rows = query("""
        SELECT DATE(created_at) AS date,
               movement_type,
               SUM(ABS(quantity))        AS total_units,
               ROUND(SUM(ABS(quantity * unit_price)), 2) AS total_value
        FROM stock_movements
        WHERE created_at >= NOW() - INTERVAL 30 DAY
        GROUP BY DATE(created_at), movement_type
        ORDER BY date ASC
    """)
    # Serialize dates
    for r in rows:
        r["date"] = str(r["date"])
    return jsonify(rows)


# ── Low Stock Alerts ───────────────────────────────────────────────────────────
@app.route("/api/dashboard/low-stock")
def low_stock_alerts():
    rows = query("""
        SELECT p.id, p.name, p.sku, p.quantity_in_stock, p.reorder_level,
               c.name AS category, s.name AS supplier,
               p.unit_price, p.unit
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        LEFT JOIN suppliers  s ON s.id = p.supplier_id
        WHERE p.quantity_in_stock <= p.reorder_level AND p.is_active = 1
        ORDER BY p.quantity_in_stock ASC
        LIMIT 20
    """)
    return jsonify(rows)


# ── Top Products by value ──────────────────────────────────────────────────────
@app.route("/api/dashboard/top-products")
def top_products():
    rows = query("""
        SELECT p.id, p.name, p.sku, p.quantity_in_stock,
               p.unit_price, p.cost_price,
               ROUND(p.quantity_in_stock * p.unit_price, 2) AS stock_value,
               ROUND((p.unit_price - p.cost_price) / p.unit_price * 100, 1) AS margin_pct,
               c.name AS category
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE p.is_active = 1
        ORDER BY stock_value DESC
        LIMIT 10
    """)
    return jsonify(rows)


# ── All Products (paginated) ───────────────────────────────────────────────────
@app.route("/api/products")
def list_products():
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    search   = request.args.get("search", "").strip()
    category = request.args.get("category", "")
    offset   = (page - 1) * per_page

    where_clauses = ["p.is_active = 1"]
    params: list = []

    if search:
        where_clauses.append("(p.name LIKE %s OR p.sku LIKE %s)")
        params += [f"%{search}%", f"%{search}%"]
    if category:
        where_clauses.append("c.name = %s")
        params.append(category)

    where = " AND ".join(where_clauses)

    total = query(
        f"SELECT COUNT(*) AS cnt FROM products p LEFT JOIN categories c ON c.id=p.category_id WHERE {where}",
        params, fetchone=True
    )["cnt"]

    rows = query(
        f"""
        SELECT p.id, p.name, p.sku, p.quantity_in_stock, p.reorder_level,
               p.unit_price, p.cost_price, p.unit, p.updated_at,
               c.name AS category, s.name AS supplier
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        LEFT JOIN suppliers  s ON s.id = p.supplier_id
        WHERE {where}
        ORDER BY p.name ASC
        LIMIT %s OFFSET %s
        """,
        params + [per_page, offset]
    )

    for r in rows:
        r["updated_at"] = str(r["updated_at"])

    return jsonify({"total": total, "page": page, "per_page": per_page, "products": rows})


# ── Single Product ─────────────────────────────────────────────────────────────
@app.route("/api/products/<int:product_id>")
def get_product(product_id):
    row = query(
        """SELECT p.*, c.name AS category, s.name AS supplier
           FROM products p
           LEFT JOIN categories c ON c.id = p.category_id
           LEFT JOIN suppliers  s ON s.id = p.supplier_id
           WHERE p.id = %s""",
        (product_id,), fetchone=True
    )
    if not row:
        return jsonify({"error": "Not found"}), 404
    row["created_at"] = str(row["created_at"])
    row["updated_at"] = str(row["updated_at"])
    return jsonify(row)


# ── Create Product ─────────────────────────────────────────────────────────────
@app.route("/api/products", methods=["POST"])
def create_product():
    data = request.json
    required = ["name", "sku", "unit_price", "cost_price"]
    missing  = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    new_id = execute(
        """INSERT INTO products (name, sku, category_id, supplier_id, description,
               unit_price, cost_price, quantity_in_stock, reorder_level, unit)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            data["name"], data["sku"],
            data.get("category_id"), data.get("supplier_id"),
            data.get("description", ""),
            data["unit_price"], data["cost_price"],
            data.get("quantity_in_stock", 0),
            data.get("reorder_level", 10),
            data.get("unit", "piece"),
        )
    )
    # Log initial stock movement if quantity > 0
    if data.get("quantity_in_stock", 0) > 0:
        execute(
            "INSERT INTO stock_movements (product_id, movement_type, quantity, unit_price) VALUES (%s,'purchase',%s,%s)",
            (new_id, data["quantity_in_stock"], data["cost_price"])
        )
    return jsonify({"id": new_id, "message": "Product created"}), 201


# ── Update Product ─────────────────────────────────────────────────────────────
@app.route("/api/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.json
    execute(
        """UPDATE products SET name=%s, sku=%s, category_id=%s, supplier_id=%s,
               description=%s, unit_price=%s, cost_price=%s,
               quantity_in_stock=%s, reorder_level=%s, unit=%s
           WHERE id=%s""",
        (
            data["name"], data["sku"],
            data.get("category_id"), data.get("supplier_id"),
            data.get("description", ""),
            data["unit_price"], data["cost_price"],
            data["quantity_in_stock"],
            data.get("reorder_level", 10),
            data.get("unit", "piece"),
            product_id,
        )
    )
    return jsonify({"message": "Updated"})


# ── Delete (soft) Product ──────────────────────────────────────────────────────
@app.route("/api/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    execute("UPDATE products SET is_active=0 WHERE id=%s", (product_id,))
    return jsonify({"message": "Deleted"})


# ── Stock Adjustment ───────────────────────────────────────────────────────────
@app.route("/api/products/<int:product_id>/adjust-stock", methods=["POST"])
def adjust_stock(product_id):
    data         = request.json
    movement     = data.get("movement_type", "adjustment")
    quantity     = int(data.get("quantity", 0))
    unit_price   = float(data.get("unit_price", 0))
    notes        = data.get("notes", "")

    if quantity == 0:
        return jsonify({"error": "Quantity cannot be zero"}), 400

    # Negative for sales/damage
    signed_qty = -abs(quantity) if movement in ("sale", "damage") else abs(quantity)

    execute(
        "UPDATE products SET quantity_in_stock = quantity_in_stock + %s WHERE id=%s",
        (signed_qty, product_id)
    )
    execute(
        "INSERT INTO stock_movements (product_id, movement_type, quantity, unit_price, notes) VALUES (%s,%s,%s,%s,%s)",
        (product_id, movement, signed_qty, unit_price, notes)
    )
    return jsonify({"message": "Stock adjusted", "change": signed_qty})


# ── Categories ─────────────────────────────────────────────────────────────────
@app.route("/api/categories")
def list_categories():
    return jsonify(query("SELECT * FROM categories ORDER BY name"))


# ── Suppliers ──────────────────────────────────────────────────────────────────
@app.route("/api/suppliers")
def list_suppliers():
    return jsonify(query("SELECT * FROM suppliers ORDER BY name"))


# ── Recent Movements ───────────────────────────────────────────────────────────
@app.route("/api/movements")
def list_movements():
    rows = query("""
        SELECT sm.id, sm.movement_type, sm.quantity, sm.unit_price,
               sm.notes, sm.created_at,
               p.name AS product_name, p.sku
        FROM stock_movements sm
        JOIN products p ON p.id = sm.product_id
        ORDER BY sm.created_at DESC
        LIMIT 50
    """)
    for r in rows:
        r["created_at"] = str(r["created_at"])
    return jsonify(rows)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
