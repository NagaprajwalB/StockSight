
# StockSight — Inventory Analytics Dashboard

A full-stack inventory analytics dashboard using Python (Flask), MySQL, and a modern HTML/JS frontend.

## Stack

| Layer    | Technology                        |
|----------|-----------------------------------|
| Backend  | Python 3.10+, Flask, mysql-connector-python |
| Database | MySQL 8.0+ (Dockerized)           |
| Frontend | HTML/CSS/JS + Chart.js            |

---


## Project Structure

```
PY-MYSQL/
├── sql/
│   └── schema.sql          # DB schema + seed data
├── backend/
│   ├── app.py              # Flask REST API
│   └── requirements.txt    # Python dependencies
├── frontend/
│   └── index.html          # Single-page dashboard
├── docker-compose.yml      # Multi-service orchestration
├── dockerfile              # Backend Dockerfile
└── README.md
```

---


## Setup

### 1. Run with Docker (Recommended)

```bash
# In project root:
docker-compose up --build
# MySQL: localhost:3307
# Backend API: http://localhost:5000
# Frontend:   http://localhost:8080
```

* MySQL data is initialized from `sql/schema.sql`.
* The backend connects to the MySQL container using the credentials in `docker-compose.yml`.
* The frontend is served via Nginx (see docker-compose).

### 2. Manual Setup (Dev)

#### MySQL Database

```bash
# Log into MySQL
mysql -u root -p
# Run schema
mysql -u root -p < sql/schema.sql
```

#### Backend (Flask API)

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
# Create .env file with DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT
python app.py
# → Running on http://0.0.0.0:5000
```

#### Frontend

Open `frontend/index.html` in your browser, or serve with:

```bash
cd frontend
python -m http.server 8080
# → Open http://localhost:8080
```

> **Note**: The frontend expects the backend at `http://localhost:5000/api`.
> If you change the backend port, update the `API` constant in `index.html`.

---


## API Endpoints

| Method | Endpoint                                 | Description                        |
|--------|------------------------------------------|------------------------------------|
| GET    | `/api/health`                            | DB connection check                |
| GET    | `/api/dashboard/kpis`                    | Key performance indicators         |
| GET    | `/api/dashboard/category-breakdown`      | Value by category                  |
| GET    | `/api/dashboard/stock-trend`             | 30-day movement trend              |
| GET    | `/api/dashboard/low-stock`               | Products at/below reorder level    |
| GET    | `/api/dashboard/top-products`            | Top 10 by stock value              |
| GET    | `/api/products`                          | Paginated product list             |
| GET    | `/api/products/<id>`                     | Single product                     |
| POST   | `/api/products`                          | Create product                     |
| PUT    | `/api/products/<id>`                     | Update product                     |
| DELETE | `/api/products/<id>`                     | Soft-delete product                |
| POST   | `/api/products/<id>/adjust-stock`        | Stock in/out/adjustment            |
| GET    | `/api/categories`                        | All categories                     |
| GET    | `/api/suppliers`                         | All suppliers                      |
| GET    | `/api/movements`                         | Recent 50 stock movements          |

---


## Features

- **Dashboard KPIs**: total products, low-stock count, inventory cost vs retail value, 30-day revenue
- **Category chart**: doughnut chart of inventory value per category
- **Movement trend**: 30-day line chart of purchases, sales, adjustments, returns, damages
- **Top products**: table ranked by stock value with margin badges
- **Low-stock alerts**: products at or below reorder level with one-click restock
- **Stock movements**: full audit trail of every transaction
- **Products catalog**: searchable, filterable, paginated table with CRUD + stock adjustments

---


## Production

For production, use Gunicorn (already in requirements.txt):

```bash
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Or deploy using Docker as above.
