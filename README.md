# DemandPilot AI

AI-powered demand forecasting and inventory optimization platform for restaurants, combining machine learning, intelligent agents, and actionable operational insights.

## Overview

DemandPilot AI is a portfolio project that demonstrates how traditional Machine Learning and Generative AI can work together to support restaurant operations.

The application will use reproducible synthetic sales data to forecast product demand, estimate ingredient requirements, identify inventory shortages, and provide actionable recommendations through an AI assistant.

## Planned Features

- Historical sales analysis and visualization.
- Product demand forecasting using Machine Learning.
- Model evaluation against a simple baseline.
- Ingredient requirements and inventory risk analysis.
- AI assistant with tool calling for data-grounded recommendations.
- Interactive dashboard with Portuguese and English support.

## Tech Stack

| Area | Technologies |
|------|-------------|
| Backend | Python, FastAPI, Pydantic, SQLAlchemy |
| Database | PostgreSQL, Alembic |
| Machine Learning | Pandas, NumPy, scikit-learn |
| Generative AI | OpenAI API, tool calling |
| Frontend | React, TypeScript, Vite |
| Infrastructure | Docker, Docker Compose, GitHub Actions |
| Testing and Quality | Pytest, Ruff |

## Project Status

**Status:** Initial development.

The application is being developed incrementally. Setup instructions, architecture details, and demonstration examples will be added as features are implemented.

## Running the API

### Requirements

- Python 3.13
- uv

### Setup

From the repository root:

```powershell
cd apps/api
uv sync
```

### Start the development server

```powershell
uv run uvicorn app.main:app --reload
```

The API will be available at:

- API: http://127.0.0.1:8000
- Health check: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs

## Running PostgreSQL

### Requirements

- Docker Engine with Docker Compose

### Setup

From the repository root, create a local environment file:

```powershell
Copy-Item apps/api/.env.example apps/api/.env
```

The example credentials are intended for local development only.

### Start PostgreSQL

```powershell
docker compose --env-file apps/api/.env up -d db
```

### Apply database migrations

From the repository root, start PostgreSQL:

```powershell
docker compose --env-file apps/api/.env up -d db
```

Then, from the API directory:

```powershell
cd apps/api
uv run alembic upgrade head
```

To check the current migration revision:

```powershell
uv run alembic current
```

Database schema changes are managed through Alembic migrations.

### Check database status

```powershell
docker compose --env-file apps/api/.env ps
```

### Stop PostgreSQL

```powershell
docker compose --env-file apps/api/.env down
```

The database uses a persistent Docker volume. Stopping the service does not delete its data.

## Demo Data

The application uses reproducible synthetic restaurant data for development and demonstration.

The dataset includes:

- One fictional restaurant.
- Five products and ten ingredients.
- Product recipes and initial inventory quantities.
- 180 days of historical sales per product.
- Weekly demand patterns, gradual growth, and controlled random variation.

### Generate Demo Data

Ensure PostgreSQL is running and migrations have been applied.

From the API directory:

```powershell
uv run python -m app.demo_data
```

The generator uses a fixed random seed and creates historical sales ending on the day before its first execution.

Running the command again does not duplicate existing demo data.

### Run Tests

```powershell
uv run pytest -q
```

All demo data is synthetic and does not represent real restaurant transactions.

## API Endpoints

The backend provides REST endpoints for accessing restaurant products and historical sales.

### List Products

```http
GET /products
```

Returns the available products.

Example response:

```json
[
  {
    "id": 1,
    "name": "Classic Burger"
  }
]
```

### Get Product Sales

```http
GET /products/{product_id}/sales
```

Returns historical daily sales for a specific product, ordered by date.

Optional query parameters:

- `start_date`: Start of the date range (YYYY-MM-DD).
- `end_date`: End of the date range (YYYY-MM-DD).

Example:

```http
GET /products/1/sales?start_date=2026-01-01&end_date=2026-01-31
```

Example response:

```json
[
  {
    "sale_date": "2026-01-01",
    "quantity": 20
  },
  {
    "sale_date": "2026-01-02",
    "quantity": 25
  }
]
```

An unknown product returns HTTP 404. Invalid date parameters or reversed date ranges return HTTP 422.

Interactive API documentation is available at:

http://127.0.0.1:8000/docs

## Demand Forecasting

The forecasting module uses historical daily sales to estimate future product demand.

### Baseline

The initial baseline predicts demand using the average of the last seven available sales observations.

It supports configurable forecast horizons and lookback windows.

The baseline serves as a reference for evaluating future Machine Learning models.

Model training, temporal validation, and evaluation metrics will be introduced in subsequent development steps.

## Data

The project will use synthetic restaurant data generated for demonstration purposes.

No real customer data or commercial restaurant integrations are required.