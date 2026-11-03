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

### Machine Learning Model

The initial Machine Learning model uses scikit-learn's Linear Regression to predict daily product demand.

Features include:

- Day index to represent historical trends.
- Day-of-week indicators to capture weekly demand patterns.

### Evaluation

Model evaluation uses a chronological 80/20 train-test split.

The model is trained only on historical observations preceding the test period.

Evaluation metrics:

- MAE (Mean Absolute Error).
- WAPE (Weighted Absolute Percentage Error).

Predictions are constrained to non-negative values.

The evaluation uses a fixed forecast origin without updating the model with test-period sales.

### Forecast Service

The forecasting service compares two prediction methods:

- Seven-day moving average baseline.
- Linear Regression with calendar-based features.

Both methods are evaluated on the same chronological holdout period using MAE and WAPE.

The method with the lowest MAE is selected. The baseline is preferred when both methods achieve the same MAE.

Future forecasts use all available historical observations after evaluation.

The service provides:

- Selected forecasting method.
- Baseline and regression evaluation metrics.
- Evaluation date range.
- Historical data cutoff date.
- Daily demand forecasts for a configurable horizon.

Forecasts start on the day following the latest available sales observation.

### Forecasting API

Demand forecasts and model evaluation metrics are available through REST endpoints.

#### Get Product Forecast

```http
GET /products/{product_id}/forecast?horizon=7
```

Returns the selected forecasting method and daily demand predictions.

The `horizon` parameter is optional and accepts values from 1 to 30 days.

#### Get Model Metrics

```http
GET /products/{product_id}/forecast/metrics
```

Returns:

- Selected forecasting method.
- Evaluation date range.
- Baseline MAE and WAPE.
- Linear Regression MAE and WAPE.

Both methods are evaluated on the same chronological holdout period.

The method with the lowest MAE is selected, with the baseline preferred in case of a tie.

Forecasts start on the day following the latest available historical observation, which may differ from the current date.

Interactive documentation is available at:

http://127.0.0.1:8000/docs

## Inventory Analysis

The inventory module calculates ingredient requirements based on expected product demand and recipe quantities.

It supports:

- Aggregation of ingredients shared across multiple products.
- Exact decimal calculations for ingredient quantities.
- Comparison between required and available stock.
- Identification of estimated ingredient shortages.
- Validation of missing recipes and inventory records.

Inventory calculations are deterministic and do not rely on Generative AI.

### Forecast-Based Inventory Analysis

The inventory service combines Machine Learning demand forecasts with restaurant recipes and current inventory records.

It performs the following steps:

1. Retrieve products and their historical sales.
2. Generate demand forecasts for the requested planning period.
3. Round daily product forecasts up to whole production units.
4. Calculate ingredient requirements across all products.
5. Compare required quantities with available inventory.
6. Identify ingredient shortages and return structured results.

The service supports planning horizons from 1 to 30 days.

Planning starts on the current date by default and can be configured explicitly. Predictions for dates before the planning period are excluded.

The latest historical sales date is included in the results to provide context about data freshness.

Inventory calculations assume the recorded stock is available for the entire planning period, without additional purchases or stock movements.

The service uses deterministic calculations and does not rely on Generative AI.

### Inventory Analysis API

The application provides a REST endpoint for forecast-based inventory risk analysis.

```http
GET /restaurants/{restaurant_id}/inventory/analysis
```

Optional query parameters:

- `start_date`: Planning start date (YYYY-MM-DD). Defaults to the current date.
- `horizon`: Number of planning days, from 1 to 30. Defaults to 1.

Example:

```http
GET /restaurants/1/inventory/analysis?start_date=2026-10-31&horizon=1
```

The response includes:

- Planning start and end dates.
- Forecasted production quantities for each product.
- Selected forecasting method and latest historical sales date.
- Required and available quantities for each ingredient.
- Estimated shortages and inventory risk indicators.

Ingredient quantities are serialized as decimal strings to preserve precision.

An unknown restaurant returns HTTP 404. Invalid planning parameters or insufficient data return HTTP 422.

The analysis is read-only and does not modify inventory quantities.

## AI Advisor

DemandPilot AI integrates Google Gemini to provide natural-language
recommendations based on demand forecasts and inventory calculations.

The assistant uses function calling to access two application tools:

- `get_product_forecast`: Retrieves product demand forecasts and evaluation metrics.
- `get_inventory_analysis`: Retrieves ingredient requirements and shortage risks.

Forecasting and inventory calculations remain the responsibility of the
backend. Gemini interprets their results but does not modify application data.

### Configuration

Generate an API key using Google AI Studio:

https://aistudio.google.com/apikey

Add the following variables to `apps/api/.env`:

```dotenv
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

The Gemini Developer API offers a free tier with usage limits.
Free-tier data may be used by Google to improve its products.
Do not submit confidential business information.

### Testing

Advisor tests use mocked Gemini responses and require no API credentials.

```powershell
cd apps/api
uv run pytest tests/test_ai_advisor.py -v
```

The assistant currently handles independent questions without persistent
conversation history.

### Chat API

Send a question to the AI advisor:

**POST** `/restaurants/{restaurant_id}/advisor/chat`

Request:

```json
{
  "message": "Which ingredients are at risk of shortage?"
}
```

Response:

```json
{
  "answer": "The inventory analysis indicates..."
}
```

The endpoint validates the restaurant and message before calling
the Gemini-powered advisor.

Responses are based on application tools for demand forecasting
and inventory analysis. No changes are made to inventory data.

Each request is independent. Conversation history is not persisted.

API documentation is available at:

http://127.0.0.1:8000/docs

### Chat API tests

```powershell
cd apps/api
uv run pytest tests/test_advisor_api.py -v
```

## Frontend

The web application uses React, TypeScript, and Vite.

### Requirements

- Node.js 22+
- npm

### Getting Started

Install frontend dependencies:

```bash
cd apps/web
npm install
```

Start the FastAPI backend separately, then start the frontend:

```bash
npm run dev
```

Open http://localhost:5173.

During local development, Vite proxies requests starting with `/api`
to the FastAPI backend at `http://127.0.0.1:8000`.

The home page displays the backend connection status.

### Validation

```bash
npm run lint
npm run build
```

### Planned Features

- Product demand forecasting dashboard
- Ingredient inventory risk analysis
- Gemini-powered AI advisor chat

Gemini credentials remain configured exclusively in the backend.

### Demand Forecasting Dashboard

The frontend provides an interactive demand forecasting dashboard.

Features:

- Select a restaurant product.
- Choose a forecast horizon of 1, 7, 14, or 30 days.
- Visualize predicted demand using a responsive line chart.
- Inspect daily predictions in a table.
- Compare MAE and WAPE for the baseline and linear regression models.
- Identify the model selected by the backend.
- View the last recorded sale date and evaluation period.

The dashboard consumes:

- `GET /products`
- `GET /products/{product_id}/forecast`

Forecasting calculations and model selection remain in the FastAPI backend.

The application uses Recharts for data visualization and the Vite
development proxy for backend communication.

### Inventory Planning Dashboard

The frontend includes an inventory planning dashboard powered by
the existing FastAPI inventory analysis service.

Features:

- Select a planning start date.
- Choose a planning horizon of 1, 7, 14, or 30 days.
- View the number of products and ingredients analyzed.
- Identify ingredients at risk of shortage.
- Compare required, available, and shortage quantities.
- Visualize inventory coverage for each ingredient.
- Review predicted production quantities for each product.

The dashboard consumes:

- `GET /restaurants/{restaurant_id}/inventory/analysis`

Inventory calculations, recipe aggregation, and forecasting remain
in the backend.

The current dashboard uses restaurant ID 1 from the demo dataset.

Quantities and dates are displayed using Brazilian Portuguese
formatting. The frontend does not update inventory records.

### Gemini AI Advisor Chat

The frontend includes an AI-powered assistant integrated with the
FastAPI backend and Google Gemini.

Features:

- Ask questions about demand forecasting and inventory risks.
- Use suggested questions to explore the demo restaurant data.
- Display Gemini responses with Markdown formatting.
- Show loading indicators while the assistant is responding.
- Handle API errors, unavailable services, and rate limits.
- Display messages during the current page session.

The chat consumes:

- `POST /restaurants/{restaurant_id}/advisor/chat`

Example request:

```json
{
  "message": "Which ingredients are at risk of shortage?"
}
```

The backend uses Gemini function calling to retrieve data from
the existing forecasting and inventory services.

Each request is independent. Previous messages are displayed in
the frontend but are not sent as conversation history.

Gemini API credentials are configured only in `apps/api/.env`.

The frontend uses `react-markdown` to render assistant responses.

### Web Dashboard

The React dashboard provides three integrated features:

- **Demand Forecasting:** View product forecasts, compare model
  evaluation metrics, and explore daily predicted demand.
- **Inventory Planning:** Analyze ingredient requirements,
  available quantities, and predicted shortages.
- **AI Advisor:** Ask Gemini questions about forecasting and
  inventory data through backend function calling.

The interface uses Brazilian Portuguese and includes responsive
layouts, keyboard navigation, loading indicators, and error states.

The application communicates with FastAPI through the Vite `/api`
proxy during local development.

Gemini credentials remain on the backend and are never exposed
to the browser.

The demo currently uses restaurant ID 1. AI chat messages are
stored only in React state and are not persisted.

## Data

The project will use synthetic restaurant data generated for demonstration purposes.

No real customer data or commercial restaurant integrations are required.