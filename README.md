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

## Data

The project will use synthetic restaurant data generated for demonstration purposes.

No real customer data or commercial restaurant integrations are required.