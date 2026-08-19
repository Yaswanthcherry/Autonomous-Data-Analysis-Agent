# Getting Started - AI Data Analyst Agent

## ⚡ 5-Minute Quick Start

### Step 1: Install Dependencies (2 min)

```bash
# Navigate to project directory
cd "c:\Users\YASWANTH\Desktop\analysis agent"

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install
```

### Step 2: Start Backend (1 min)

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

✅ Backend ready at: `http://localhost:8000`
✅ API docs at: `http://localhost:8000/docs`

### Step 3: Start Frontend (1 min)

Open **new terminal**:
```bash
cd frontend
npm run dev
```

✅ Frontend ready at: `http://localhost:3000`

### Step 4: Access the Application (1 min)

1. Open browser: `http://localhost:3000`
2. Login (create account or use demo credentials)
3. Click "Upload Dataset"
4. Select a CSV file
5. Click "Analyze"
6. Watch the 13-stage pipeline execute
7. Review results, charts, and PDF

**That's it! You're running the full AI Data Analyst Agent.** 🎉

---

## 📊 What Happens Next

### After You Click "Analyze"

The system automatically executes a 13-stage pipeline:

```
1. Planning (5%)
   └─ Detect: task type, target column, problem classification

2. Profiling (10%)
   └─ Compute: data shape, quality metrics, column types

3. Cleaning (18%)
   └─ Handle: nulls, duplicates, normalize data

4. Anomaly Detection (26%)
   └─ Find: outliers using Isolation Forest

5. Exploratory Analysis (34%)
   └─ Compute: correlations, distributions, skewness

6. Visualizations (44%)
   └─ Generate: 10+ interactive charts

7-11. AI Analysis & Insights (54-84%)
   └─ Train ML models, generate business insights

12. PDF Export (96%)
   └─ Create professional report

13. Complete (100%)
   └─ Ready for follow-up chat questions
```

---

## 🧪 Test with Sample Data

### Option 1: Use Built-in Test Dataset

```python
# Create sample data
import pandas as pd

# Classification example
data = pd.DataFrame({
    'age': [25, 35, 45, 28, 32, 45, 50, 23, 38, 42],
    'income': [30000, 50000, 70000, 35000, 45000, 65000, 75000, 28000, 55000, 68000],
    'education': ['HS', 'BS', 'MS', 'HS', 'BS', 'MS', 'PhD', 'HS', 'BS', 'MS'],
    'purchased': ['No', 'Yes', 'Yes', 'No', 'Yes', 'Yes', 'Yes', 'No', 'Yes', 'Yes']
})

data.to_csv('test_data.csv', index=False)
```

Then upload `test_data.csv` via web interface.

### Option 2: Download Sample Datasets

Popular datasets to try:
- [Iris Dataset](https://archive.ics.uci.edu/ml/datasets/iris) (classification)
- [Titanic Dataset](https://www.kaggle.com/c/titanic/data) (binary classification)
- [Diabetes Dataset](https://www.kaggle.com/datasets/akshayvsingh/diabetes) (regression)
- [Diabetes Dataset](https://www.kaggle.com/datasets/uciml/breast-cancer-wisconsin-data) (classification)

---

## 🔐 Authentication

### First Time Setup

```bash
# Create admin user
cd backend
python scripts/create_admin.py
```

Follow prompts to set username and password.

### Login with Credentials

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## 🛠️ Troubleshooting

### Backend Won't Start

**Problem**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
cd backend
pip install -r requirements.txt
```

### Frontend Won't Start

**Problem**: `Command not found: npm`

**Solution**: Install Node.js from https://nodejs.org/

```bash
# Verify installation
node --version
npm --version

# Try again
npm install
npm run dev
```

### Port Already in Use

**Problem**: `Address already in use: ('0.0.0.0', 8000)`

**Solution**: Kill existing process or use different port

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different port
python -m uvicorn main:app --port 8001
```

### Database Error

**Problem**: `sqlite database locked`

**Solution**: Database lock usually resolves itself. If persistent:

```bash
# Remove database file (warning: loses data)
cd backend
rm analyst.db

# Restart app (new database will be created)
python -m uvicorn main:app --reload
```

---

## 📚 Project Structure Overview

### Backend (`backend/`)
- `agents/` - 8 specialized AI agents (NEW)
- `services/` - Core business logic
- `api/` - REST endpoints
- `models/` - Database models
- `core/` - Configuration & middleware
- `main.py` - FastAPI application
- `requirements.txt` - Python dependencies

### Frontend (`frontend/`)
- `src/app/` - Pages (dashboard, analysis, reports)
- `src/components/` - Reusable React components
- `src/lib/` - API client, utilities
- `package.json` - Node dependencies

---

## 📖 Documentation Guide

| Document | Read When |
|----------|-----------|
| **QUICKSTART.md** | Want quick setup instructions |
| **README.md** | Want project overview |
| **ARCHITECTURE.md** | Want to understand the design |
| **PROJECT_STATUS.md** | Want detailed implementation status |
| **DEPLOYMENT.md** | Want to deploy to production |
| **COMPLETION_SUMMARY.md** | Want to see what was completed |

---

## 🔄 Common Workflows

### Workflow 1: Upload and Analyze

```bash
# 1. Get authentication token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.access_token')

# 2. Upload dataset
DATASET=$(curl -X POST http://localhost:8000/api/v1/datasets/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@data.csv" | jq -r '.id')

# 3. Start analysis
JOB=$(curl -X POST http://localhost:8000/api/v1/analysis/$DATASET/analyze \
  -H "Authorization: Bearer $TOKEN" | jq -r '.job_id')

# 4. Check progress
curl http://localhost:8000/api/v1/analysis/$JOB \
  -H "Authorization: Bearer $TOKEN"

# 5. Get results when complete
curl http://localhost:8000/api/v1/analysis/$JOB/results \
  -H "Authorization: Bearer $TOKEN"

# 6. Download PDF report
curl http://localhost:8000/api/v1/analysis/$JOB/report \
  -H "Authorization: Bearer $TOKEN" > report.pdf
```

### Workflow 2: Ask Follow-up Questions

```bash
# Chat about analysis results
curl -X POST http://localhost:8000/api/v1/chat/$JOB/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the top 3 features?"}'
```

### Workflow 3: Export Results

```bash
# Export analysis as JSON
curl http://localhost:8000/api/v1/analysis/$JOB/export \
  -H "Authorization: Bearer $TOKEN" > analysis.json

# Export PDF report
curl http://localhost:8000/api/v1/analysis/$JOB/report \
  -H "Authorization: Bearer $TOKEN" > report.pdf

# Export charts as images
curl http://localhost:8000/api/v1/analysis/$JOB/charts/export \
  -H "Authorization: Bearer $TOKEN" > charts.zip
```

---

## 🚀 Next Steps

### Week 1: Learn and Explore
1. ✅ Setup locally (this guide)
2. ✅ Upload sample datasets
3. ✅ Review generated reports
4. ✅ Explore API documentation
5. ✅ Read technical documentation

### Week 2: Integration
1. Test with your own datasets
2. Integrate with your applications
3. Customize visualizations
4. Setup monitoring
5. Plan Phase 2 deployment

### Week 3+: Production
1. Deploy to staging environment
2. Load test with realistic data
3. Setup monitoring & alerting
4. Configure backups
5. Deploy to production

---

## 💡 Tips & Tricks

### Tip 1: Monitor Progress in Real Time
```bash
# Watch logs in real time
docker logs -f analyst_backend  # if using Docker

# Or directly
tail -f backend/logs/app.log
```

### Tip 2: Debug Failed Analysis
```bash
# Check job status and error message
curl http://localhost:8000/api/v1/analysis/{job_id} \
  -H "Authorization: Bearer $TOKEN" | jq '.error_message'

# Check analysis results for partial data
curl http://localhost:8000/api/v1/analysis/{job_id}/results \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

### Tip 3: Clear Data for Fresh Start
```bash
# Reset database (development only)
cd backend
rm analyst.db  # Fresh SQLite database

# Create new admin user
python scripts/create_admin.py

# Restart app
python -m uvicorn main:app --reload
```

### Tip 4: Profile Slow Operations
```python
# Add timing to understand bottlenecks
import time

start = time.time()
# ... operation ...
elapsed = time.time() - start
logger.info(f"Operation took {elapsed:.2f} seconds")
```

---

## 🎯 Success Criteria

After setup, you should be able to:

- ✅ Access web interface at `http://localhost:3000`
- ✅ Login with credentials
- ✅ Upload a CSV file
- ✅ See analysis progress (5% → 100%)
- ✅ View generated charts
- ✅ Download PDF report
- ✅ Ask chat questions about results
- ✅ See API documentation at `http://localhost:8000/docs`

---

## 🆘 Need Help?

### Resources
- 📖 **Documentation**: See `README.md` and `ARCHITECTURE.md`
- 🐛 **Issues**: Check `TROUBLESHOOTING.md` or logs
- 💬 **Questions**: Review API docs at `http://localhost:8000/docs`
- 📧 **Support**: See project documentation

### Quick Help

**Backend not responding?**
```bash
curl http://localhost:8000/health
```

**Database issues?**
```bash
cd backend
python -c "from core.database import engine; engine.connect()"
```

**Frontend not loading?**
```bash
cd frontend
npm run build  # Check for build errors
npm run dev    # Restart dev server
```

---

## ✨ What Happens Under the Hood

When you upload a dataset, here's what the AI analyst does:

1. **Planning** - Detects if it's classification, regression, clustering, or time-series
2. **Profiling** - Analyzes data quality, types, and statistics
3. **Cleaning** - Handles missing values, duplicates, outliers
4. **Analysis** - Computes correlations, distributions, patterns
5. **Visualization** - Generates interactive charts
6. **ML Training** - Trains 4 models: Logistic Regression, Random Forest, XGBoost, LightGBM
7. **Insights** - Uses AI (OpenAI GPT-4o) to generate human-readable findings
8. **Report** - Creates professional PDF with all results
9. **Chat** - Ready to answer follow-up questions

All **automatically**. No configuration needed.

---

## 🎉 Ready to Go!

You now have a **production-ready autonomous AI data analyst** running locally. 

### Next: Pick Your Path

**Path 1: Try It Out**
- Upload datasets
- Explore results
- Review reports
- Ask chat questions

**Path 2: Integrate It**
- Use API endpoints
- Build custom workflows
- Embed in applications
- Extend functionality

**Path 3: Deploy It**
- Follow DEPLOYMENT.md
- Setup production infrastructure
- Configure monitoring
- Scale to production

---

## 📞 Quick Reference

### Common Commands

```bash
# Start backend
cd backend && python -m uvicorn main:app --reload

# Start frontend
cd frontend && npm run dev

# View API docs
http://localhost:8000/docs

# Check health
curl http://localhost:8000/health

# View logs
tail -f backend/logs/app.log

# Run tests
cd backend && pytest -v

# Format code
black backend/

# Check types
mypy backend/
```

### Useful Ports

- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs`
- **Database**: SQLite at `backend/analyst.db`
- **Logs**: `backend/logs/app.log`

---

**You're all set! Happy analyzing! 🚀**

For more details, see:
- Quick details: QUICKSTART.md
- Full guide: DEPLOYMENT.md
- Architecture: ARCHITECTURE.md
