# DemandPilot AI

DemandPilot AI is a restaurant demand forecasting and inventory planning demo. Its Portuguese-language dashboard shows product forecasts, estimates ingredient shortages, and includes a Gemini assistant that answers questions using the application's forecasting and inventory tools.

## Demand forecasting and inventory

The API trains a scikit-learn linear regression model for each product. It uses the day index to capture trends and day-of-week indicators to capture weekly seasonality. The baseline repeats the average of the last seven available observations across the forecast horizon.

The first 80% of each product's sales history is used for training and the last 20% for evaluation. Both methods are scored on the same holdout period using mean absolute error (MAE) and weighted absolute percentage error (WAPE). The API selects the method with the lower MAE and uses the baseline in a tie. WAPE is undefined when total demand in the holdout period is zero.

The selected method uses the full history to forecast from the day after the last recorded sale. Predictions are clamped to zero or above. Inventory planning rounds each daily product forecast up to whole units, aggregates ingredient needs across recipes, and compares them with the available stock.

## Gemini assistant

The backend uses the Google Gen AI SDK with the model configured in `GEMINI_MODEL`, which defaults to `gemini-3.5-flash-lite`. The assistant calls an application tool before answering.

- `get_product_forecast` retrieves demand forecasts and evaluation metrics for a product in the demo restaurant.
- `get_inventory_analysis` retrieves projected production, ingredient requirements, and shortage risks.

The backend validates tool arguments and runs the same services that power the dashboard. Gemini explains the results in the language of the question. The dashboard displays the chat history for the current page session. Each API request handles one question independently.

Both assistant tools support horizons of 1–7 days. The dashboard endpoints support 1–30 days, with defaults of 7 days for forecasting and 1 day for inventory. Set `GEMINI_API_KEY` in `apps/api/.env` to enable live chat. Tests use mocked Gemini responses and require no API key.

## Synthetic dataset

The initial seed creates a fictional restaurant and 180 days of sales ending yesterday in the `America/Sao_Paulo` time zone.

| Data | Initial records | Details |
| --- | ---: | --- |
| Restaurant | 1 | DemandPilot Demo |
| Products | 5 | Classic Burger (32), Chicken Sandwich (22), Veggie Burger (14), French Fries (40), and Lemonade (28). The numbers are base units per day before adjustments. |
| Ingredients | 10 | Measured in units or grams. Examples include buns, beef patties, potatoes, and sugar. |
| Recipe entries | 16 | Each entry links a product to one ingredient and specifies the amount per serving. French Fries use 180 g of potatoes per serving. |
| Inventory balances | 10 | One per ingredient, such as 75 buns or 9,000 g of potatoes. |
| Daily sales | 900 | One quantity per product per day for 180 days. |

The generator multiplies each product's base demand by the following factors, rounds the result to a whole number, and clamps it to zero or above.

| Factor | How it works |
| --- | --- |
| Growth trend | The multiplier starts at `1.000` and increases by `0.001` per day. It reaches `1.179` on day 180. |
| Weekly seasonality | Monday `0.85`, Tuesday `0.95`, Wednesday `1.00`, Thursday `1.05`, Friday `1.20`, Saturday `1.50`, and Sunday `1.30`. |
| Random variation | A uniformly sampled multiplier between `0.90` and `1.10` adds day-to-day variability. The fixed random seed `42` makes the same date window reproducible. |

After the initial CLI seed, click **Atualizar dados da demo** in the dashboard to fill missing sales in the latest 180-day window through yesterday. The refresh preserves existing sales, recipes, and stock balances. Once the window is complete, repeating the refresh adds zero records. The button requires `DEMO_REFRESH_ENABLED=true` in `apps/api/.env`. The example file already sets it. If you already have an `.env` file, add the variable and restart the API.

## Project structure

```text
demandpilot-ai/
├── .github/
│   └── workflows/            # API and web checks in GitHub Actions
├── apps/
│   ├── api/
│   │   ├── alembic/          # PostgreSQL schema migrations
│   │   ├── app/
│   │   │   ├── agents/       # Gemini advisor and tool calls
│   │   │   ├── core/         # Settings, database sessions, planning defaults
│   │   │   ├── forecasting/  # Baseline, regression, and evaluation
│   │   │   ├── inventory/    # Ingredient requirements and shortage risk
│   │   │   ├── routes/       # FastAPI endpoints
│   │   │   ├── schemas/      # Pydantic request and response models
│   │   │   ├── demo_data.py  # Synthetic dataset seed and sales refresh
│   │   │   ├── main.py       # FastAPI entry point
│   │   │   └── models.py     # SQLAlchemy models
│   │   ├── tests/            # Pytest unit and API tests
│   │   ├── .env.example      # Local database and Gemini settings
│   │   ├── pyproject.toml
│   │   └── uv.lock
│   └── web/
│       ├── src/
│       │   ├── api/           # HTTP clients
│       │   ├── components/    # Forecast, inventory, and chat panels
│       │   └── App.tsx        # Dashboard and demo refresh button
│       ├── package.json
│       ├── package-lock.json
│       └── vite.config.ts    # Development proxy and build settings
├── AGENTS.md                 # Vercel deployment plan
├── compose.yaml              # Local PostgreSQL service
└── README.md
```

## Dependencies

| Area | Dependencies |
| --- | --- |
| API | Python 3.13, FastAPI, Pydantic, pydantic-settings, and Uvicorn |
| Database | PostgreSQL 17, SQLAlchemy, psycopg 3, Alembic, and Docker Compose for local development |
| Forecasting and AI | NumPy, pandas, scikit-learn, and Google Gen AI SDK (`google-genai`) |
| Web | Node.js 22, npm, React 19, TypeScript, Vite 8, Recharts, and react-markdown |
| Quality | Pytest, HTTPX2 for API tests, Ruff, ESLint, and GitHub Actions |

The dependency manifests and lockfiles are in `apps/api` and `apps/web`.

## Run locally

Install Python 3.13, uv, an up-to-date Node.js 22 with npm, and Docker with Compose.

From the repository root, copy the environment example on first setup and start PostgreSQL.

```powershell
Copy-Item apps/api/.env.example apps/api/.env
docker compose --env-file apps/api/.env up -d --wait db
```

In one terminal, go to `apps/api`, install dependencies, migrate and seed the database, then start the API.

```powershell
cd apps/api
uv sync --locked
uv run --locked alembic upgrade head
uv run --locked python -m app.demo_data
uv run --locked uvicorn app.main:app --reload
```

In a second terminal, go to `apps/web` and start the dashboard.

```powershell
cd apps/web
npm ci
npm run dev
```

Open <http://localhost:5173>. Vite forwards `/api/*` to the FastAPI server on port 8000. The endpoint reference is available in [local Swagger UI](http://127.0.0.1:8000/docs).

## Tests and quality checks

Run these checks from `apps/api`.

```powershell
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q
```

The API suite covers reproducible demo data, refresh idempotency, chronological evaluation, model selection, MAE and WAPE, recipe aggregation, inventory calculations, and HTTP contracts. Database-backed API tests use in-memory SQLite. Advisor tests cover tool calls, validation, missing credentials, and rate limits using mocks.

Run these checks from `apps/web`.

```powershell
npm run lint
npm run build
```

The web build also checks TypeScript types.
