# 🤖 AI Data Analyst Agent

An autonomous AI-powered data analysis platform. Upload a dataset and the system automatically profiles, cleans, detects anomalies, runs EDA, generates charts, trains ML models, compares them, and generates a full PDF report with business insights — all powered by GPT-4o.

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, React Query, Plotly.js |
| Backend | FastAPI, Python 3.11, Celery, SQLAlchemy 2.0 |
| Database | PostgreSQL 15 |
| Queue | Redis 7 + Celery |
| ML | Scikit-learn, XGBoost, LightGBM, Pandas |
| Charts | Plotly |
| AI | OpenAI GPT-4o |
| PDF | ReportLab |
| Auth | JWT (access + refresh tokens) |
| Deploy | Docker Compose, Nginx |

## Quick Start

### 1. Clone & configure

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

### 2. Start with Docker Compose

```bash
docker-compose up --build
```

### 3. Run DB migrations

```bash
docker-compose exec backend alembic upgrade head
```

### 4. Open the app

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- API via nginx: http://localhost/api/

## Pipeline Stages

1. Dataset Profiling — shape, dtypes, nulls, statistics
2. Data Cleaning — fill nulls, drop duplicates, parse datetimes
3. Anomaly Detection — IQR, Z-score, Isolation Forest
4. Exploratory Data Analysis — correlations, skewness, class balance
5. Chart Generation — histograms, boxplots, heatmaps, scatter matrix
6. AI Findings — GPT-4o explains patterns and issues
7. Feature Recommendations — GPT-4o recommends features and transforms
8. Model Training — LR, RF, XGBoost, LightGBM (classification + regression)
9. Model Comparison — accuracy/F1/ROC-AUC or RMSE/MAE/R²
10. Business Insights — GPT-4o generates actionable business insights
11. Executive Summary — GPT-4o writes a 200-300 word summary
12. PDF Export — full report exported as PDF
13. Chat — ask follow-up questions about your data

## Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
celery -A tasks.celery_app worker --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Tests

```bash
cd backend && pytest -v
cd frontend && npm test
```

## Project Structure

```
.
├── backend/
│   ├── api/v1/endpoints/   # auth, datasets, analysis, chat, reports
│   ├── core/               # config, db, security, logging, dependencies
│   ├── models/             # SQLAlchemy models
│   ├── services/           # profiler, cleaner, anomaly, eda, chart, ml, ai, pdf
│   ├── tasks/              # Celery pipeline
│   ├── alembic/            # DB migrations
│   └── tests/              # pytest suite
├── frontend/
│   └── src/
│       ├── app/            # Next.js App Router pages
│       ├── components/     # React components
│       └── lib/            # API client, utils, auth
├── nginx/
├── docker-compose.yml
└── .env.example
```

## Environment Variables

See `.env.example` for all required variables. Key ones:

- `OPENAI_API_KEY` — your OpenAI API key (required)
- `SECRET_KEY` — JWT signing secret (change in production)
- `POSTGRES_*` — database credentials
- `NEXT_PUBLIC_API_URL` — backend URL for the frontend
