# Quick Start Guide - AI Data Analyst Agent

## 🎯 What This Project Does

Autonomous AI-powered data analysis platform that:
- Automatically detects dataset type, target column, and problem type
- Profiles and cleans data
- Performs exploratory data analysis
- Generates interactive visualizations
- Trains and compares ML models
- Generates AI-powered insights
- Exports professional PDF reports
- Answers follow-up questions via chat

## ⚡ Quick Setup

### 1. Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start Backend Server
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

### 3. Start Frontend Server (in another terminal)
```bash
cd frontend
npm install  # if not already done
npm run dev
```

Frontend will be available at: `http://localhost:3000`

## 📊 How to Use

### Via Web Interface
1. Open `http://localhost:3000` in browser
2. Login (create account or use test credentials)
3. Click "Upload Dataset"
4. Select CSV/Excel/JSON file
5. Click "Analyze"
6. Watch real-time analysis progress
7. View results, charts, and insights
8. Download PDF report
9. Ask follow-up questions in chat

### Via API (curl examples)

#### Upload and Analyze Dataset
```bash
curl -X POST http://localhost:8000/api/v1/datasets/upload \
  -F "file=@data.csv" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get Analysis Results
```bash
curl http://localhost:8000/api/v1/analysis/{job_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get Generated Charts
```bash
curl http://localhost:8000/api/v1/analysis/{job_id}/charts \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get PDF Report
```bash
curl http://localhost:8000/api/v1/analysis/{job_id}/report \
  -H "Authorization: Bearer YOUR_TOKEN" > report.pdf
```

## 📚 Project Structure

```
analysis-agent/
├── backend/                    # FastAPI backend
│   ├── agents/                 # 8 analysis agents (NEW)
│   │   ├── planner_agent.py    # Task detection
│   │   ├── profiler_agent.py   # Dataset profiling
│   │   ├── cleaner_agent.py    # Data cleaning
│   │   ├── eda_agent.py        # Exploratory analysis
│   │   ├── visualization_agent.py  # Charts
│   │   ├── ml_agent.py         # Model training
│   │   ├── insight_agent.py    # AI insights
│   │   ├── report_agent.py     # PDF generation
│   │   └── schemas.py          # Typed I/O contracts
│   ├── services/               # Business logic
│   ├── api/                    # API endpoints
│   ├── models/                 # Database models
│   ├── tasks/
│   │   └── pipeline.py         # 13-stage orchestration
│   ├── main.py                 # FastAPI app
│   └── requirements.txt         # Python dependencies
│
├── frontend/                   # Next.js 14 frontend
│   ├── src/
│   │   ├── app/                # Pages
│   │   ├── components/         # React components
│   │   └── lib/                # Utilities
│   ├── package.json            # Node dependencies
│   └── next.config.js          # Next.js config
│
├── PROJECT_STATUS.md           # Detailed status
└── QUICKSTART.md               # This file
```

## 🔄 13-Stage Analysis Pipeline

1. **Planning** - Detect task type (classification/regression/clustering/time-series)
2. **Profiling** - Compute statistics and data quality metrics
3. **Cleaning** - Handle missing values, duplicates, outliers
4. **Anomaly Detection** - Identify unusual patterns
5. **EDA** - Exploratory data analysis (correlations, distributions)
6. **Visualizations** - Generate 5-10 interactive charts
7. **Initial Insights** - AI-powered findings (no model data)
8. **Model Training** - Train LR, RF, XGBoost, LightGBM
9. **Model Comparison** - Compare metrics, select best
10. **Final Insights** - Business insights with model results
11. **Feature Recommendations** - Suggested improvements
12. **PDF Export** - Generate professional report
13. **Complete** - Ready for chat questions

Monitor progress: Backend logs show `progress: 5% -> 10% -> 18% -> ... -> 100%`

## 🔐 Authentication

### Create Admin User (First Time)
```bash
cd backend
python scripts/create_admin.py
```

### Login with Credentials
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your_password"
  }'
```

Returns: `{"access_token": "...", "token_type": "bearer"}`

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest -v --tb=short
```

### Backend Linting
```bash
cd backend
flake8 . --max-line-length=100
```

## 📊 Example Dataset

Try with any CSV file with:
- 3+ columns
- 20+ rows
- Mix of numeric and categorical columns (optional)

Example:
```csv
age,income,education,purchased
25,30000,High School,No
35,50000,Bachelor,Yes
45,70000,Master,Yes
28,35000,High School,No
```

## 🚀 Environment Variables

Backend (`.env`):
```
DATABASE_URL=sqlite:///./analyst.db
OPENAI_API_KEY=your_key_here
JWT_SECRET_KEY=your_secret
UPLOAD_DIR=./uploads
LOG_LEVEL=INFO
```

Frontend (`.env.local`):
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"
Solution: Install requirements
```bash
cd backend
pip install -r requirements.txt
```

### "Connection refused on port 8000"
Solution: Check if backend is running
```bash
# Verify the backend is running:
curl http://localhost:8000/health
```

### "Frontend can't connect to backend"
Solution: Check API URL in `.env.local`
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### "CORS errors in browser console"
Solution: Backend CORS is configured. Make sure:
1. Frontend URL matches `ORIGINS` in `backend/core/config.py`
2. Backend is running
3. Clear browser cache

### "PDF export fails"
Solution: Check `/uploads` directory exists and is writable
```bash
mkdir -p backend/uploads
```

## 📈 Performance Tips

1. **Large files** (>100MB): Use PostgreSQL instead of SQLite
   - Edit `DATABASE_URL` to use PostgreSQL
   
2. **Slow analysis**: Enable Celery workers
   - Install Redis: `brew install redis` (Mac) or `choco install redis` (Windows)
   - Start Celery worker: `celery -A tasks.celery_app worker --loglevel=info`

3. **Multiple concurrent uploads**: Deploy with Docker
   - See Phase 2 deployment guide

## 📚 API Documentation

Swagger UI: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`

## 🎯 Common Tasks

### Upload and Get Analysis
```python
import requests

# Login
resp = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'username': 'admin',
    'password': 'password'
})
token = resp.json()['access_token']

# Upload
headers = {'Authorization': f'Bearer {token}'}
files = {'file': open('data.csv', 'rb')}
resp = requests.post('http://localhost:8000/api/v1/datasets/upload', 
                     files=files, headers=headers)
dataset_id = resp.json()['id']

# Start analysis
resp = requests.post(f'http://localhost:8000/api/v1/analysis/{dataset_id}/analyze',
                     headers=headers)
job_id = resp.json()['job_id']

# Poll for results
import time
while True:
    resp = requests.get(f'http://localhost:8000/api/v1/analysis/{job_id}',
                       headers=headers)
    status = resp.json()['status']
    if status == 'completed':
        print("✓ Analysis complete!")
        break
    elif status == 'failed':
        print("✗ Analysis failed")
        break
    time.sleep(2)
```

## 🔗 Links

- API Docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:3000`
- Backend Health: `http://localhost:8000/health`
- Project Status: See `PROJECT_STATUS.md`
- Architecture: See `PROJECT_STATUS.md`

## ✅ Next Steps

1. ✅ Start both servers
2. ✅ Upload a test dataset
3. ✅ Monitor analysis progress
4. ✅ Review results and PDF
5. ✅ Ask follow-up questions
6. 📋 [Phase 2] Deploy with Docker & PostgreSQL
7. 📋 [Phase 3] Scale with Kubernetes & Redis

## 📞 Support

- Check logs: `backend/logs/app.log`
- API docs: `http://localhost:8000/docs`
- GitHub issues: [Create an issue]
- Documentation: `PROJECT_STATUS.md`

---

**Ready to analyze? Start the servers and upload your dataset!** 🚀
