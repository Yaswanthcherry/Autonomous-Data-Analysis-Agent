# Technical Architecture - AI Data Analyst Agent

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js 14)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Pages      │ Components    │ Services      │ State     │  │
│  │  Dashboard  │ Upload        │ api.ts        │ React     │  │
│  │  Analysis   │ Charts        │ auth.ts       │ Query     │  │
│  │  Reports    │ Chat          │ cache.ts      │ Context   │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────┬────────────────────────────────────────────┘
                   │ HTTP/JSON
         ┌─────────┴────────┐
         │                  │
         ▼                  ▼
    ┌─────────────────────────────────────────────────────────┐
    │        BACKEND API (FastAPI + Python 3.11+)            │
    ├─────────────────────────────────────────────────────────┤
    │  ┌────────────────────────────────────────────────────┐ │
    │  │          API LAYER (v1)                           │ │
    │  ├────────────────────────────────────────────────────┤ │
    │  │ • /auth         - JWT authentication              │ │
    │  │ • /datasets     - Upload, list, delete datasets   │ │
    │  │ • /analysis     - Start, status, results          │ │
    │  │ • /charts       - Retrieve generated charts       │ │
    │  │ • /reports      - PDF download                    │ │
    │  │ • /chat         - Follow-up questions             │ │
    │  │ • /users        - User management                 │ │
    │  └────────────────────────────────────────────────────┘ │
    │  ┌────────────────────────────────────────────────────┐ │
    │  │        AGENT ORCHESTRATION LAYER (NEW)            │ │
    │  ├────────────────────────────────────────────────────┤ │
    │  │ 1. PlannerAgent      - Task detection              │ │
    │  │ 2. ProfilerAgent     - Data profiling              │ │
    │  │ 3. CleanerAgent      - Data cleaning               │ │
    │  │ 4. EDAAgent          - Exploratory analysis        │ │
    │  │ 5. VisualizationAgent - Chart generation           │ │
    │  │ 6. MLAgent           - Model training              │ │
    │  │ 7. InsightAgent      - AI insights                 │ │
    │  │ 8. ReportAgent       - PDF generation              │ │
    │  │                                                    │ │
    │  │ PipelineContext threads through all agents         │ │
    │  │ Each agent: Single Responsibility + Type-Safe I/O  │ │
    │  └────────────────────────────────────────────────────┘ │
    │  ┌────────────────────────────────────────────────────┐ │
    │  │          SERVICE LAYER (Core Logic)               │ │
    │  ├────────────────────────────────────────────────────┤ │
    │  │ • DataProfiler       - Statistics & quality       │ │
    │  │ • DataCleaner        - Null/duplicate handling    │ │
    │  │ • EDAService         - Correlation & skewness     │ │
    │  │ • ChartService       - Plotly generation          │ │
    │  │ • MLService          - Model training             │ │
    │  │ • PDFService         - Report generation          │ │
    │  │ • AIService          - OpenAI integration         │ │
    │  │ • AnomalyDetector    - Isolation Forest           │ │
    │  └────────────────────────────────────────────────────┘ │
    │  ┌────────────────────────────────────────────────────┐ │
    │  │        DATA ACCESS LAYER (Models)                 │ │
    │  ├────────────────────────────────────────────────────┤ │
    │  │ • User               - Authentication              │ │
    │  │ • Dataset            - Upload metadata             │ │
    │  │ • AnalysisJob        - Pipeline execution state    │ │
    │  │ • AnalysisResult     - Stage outputs              │ │
    │  │ • Chart              - Generated visualizations    │ │
    │  │ • MLModel            - Trained models              │ │
    │  │ • Report             - PDF exports                 │ │
    │  └────────────────────────────────────────────────────┘ │
    │  ┌────────────────────────────────────────────────────┐ │
    │  │          CORE LAYER (Infrastructure)              │ │
    │  ├────────────────────────────────────────────────────┤ │
    │  │ • Configuration      - Environment variables       │ │
    │  │ • Database           - SQLAlchemy + migrations     │ │
    │  │ • Security           - JWT + password hashing      │ │
    │  │ • Error Handling     - Retry logic & circuit break │ │
    │  │ • Logging            - loguru structured logs      │ │
    │  │ • Dependencies       - FastAPI dependency inject   │ │
    │  └────────────────────────────────────────────────────┘ │
    │  ┌────────────────────────────────────────────────────┐ │
    │  │      BACKGROUND TASKS (Development)               │ │
    │  ├────────────────────────────────────────────────────┤ │
    │  │ • Celery app configuration                        │ │
    │  │ • Background task executor                        │ │
    │  │ • In-memory pipeline (sync for development)       │ │
    │  │ → Redis + Celery workers for production           │ │
    │  └────────────────────────────────────────────────────┘ │
    └─────────────────────────────────────────────────────────┘
                   │ Data Persistence
         ┌─────────┴────────┐
         │                  │
         ▼                  ▼
    ┌─────────────────────────────────────────────────────────┐
    │        DATA LAYER (Database)                            │
    ├─────────────────────────────────────────────────────────┤
    │ • Development: SQLite (./analyst.db)                    │
    │ • Production:  PostgreSQL                               │
    │ • Migrations:  Alembic                                  │
    │ • ORM:         SQLAlchemy 2.0                           │
    └─────────────────────────────────────────────────────────┘
```

---

## 🔄 Request Flow

### 1. User Uploads Dataset

```
User (Frontend)
    ↓ POST /datasets/upload
Backend API (datasets.py)
    ├─ Validate JWT token
    ├─ Store file in UPLOAD_DIR
    ├─ Create Dataset record
    ├─ Create AnalysisJob record (status=pending)
    └─ Return dataset_id
User (Frontend)
    ↓ POST /analysis/{dataset_id}/analyze
Backend API (analysis.py)
    └─ Enqueue task: run_analysis_pipeline(job_id, dataset_id, file_path, file_type)
```

### 2. Pipeline Execution (Async/Background)

```
Celery Worker (or sync in dev)
    │
    ├─ Load dataset (CSV/Excel/JSON)
    │
    ├─ Stage 1: PlannerAgent
    │  └─ Detects: task_type, target_column, recommended_steps
    │  └─ Save to AnalysisResult(result_type="planner")
    │
    ├─ Stage 2: ProfilerAgent
    │  └─ Profile dataset (shape, memory, columns)
    │  └─ Save to AnalysisResult(result_type="profile")
    │
    ├─ Stage 3: CleanerAgent
    │  └─ Clean data (nulls, duplicates, datetime parsing)
    │  └─ Save to AnalysisResult(result_type="cleaning")
    │
    ├─ Stage 4: AnomalyDetector
    │  └─ Detect outliers (Isolation Forest)
    │  └─ Save to AnalysisResult(result_type="anomalies")
    │
    ├─ Stage 5: EDAAgent
    │  └─ Compute correlations, skewness, cardinality
    │  └─ Save to AnalysisResult(result_type="eda")
    │
    ├─ Stage 6: VisualizationAgent
    │  └─ Generate 5-10 Plotly charts
    │  └─ Save to Chart table (multiple rows, one per chart)
    │
    ├─ Stage 7: InsightAgent (initial)
    │  └─ AI findings (without model results)
    │  └─ Save to AnalysisResult(result_type="findings")
    │
    ├─ Stage 8-9: MLAgent (train + compare)
    │  └─ Train 4 models: LR, RF, XGBoost, LightGBM
    │  └─ Save to MLModel table (multiple rows, one per model)
    │
    ├─ Stage 10: InsightAgent (final)
    │  └─ AI insights with model results
    │  └─ Save to AnalysisResult(result_type="business_insights")
    │
    ├─ Stage 11: ReportAgent
    │  └─ Generate PDF with all results
    │  └─ Save to Report table
    │
    └─ Update AnalysisJob(status="completed", progress=100)
```

### 3. User Retrieves Results

```
User (Frontend)
    ↓ GET /analysis/{job_id}
Backend API (analysis.py)
    ├─ Query AnalysisJob
    └─ Return status, progress, current_stage
    
User (Frontend)
    ↓ GET /analysis/{job_id}/results
Backend API
    ├─ Query AnalysisResult
    ├─ Query MLModel
    ├─ Query Chart
    └─ Return all results as JSON
    
User (Frontend)
    ↓ GET /analysis/{job_id}/report
Backend API
    ├─ Query Report
    └─ Stream PDF file
    
User (Frontend)
    ↓ POST /chat/{job_id}
Backend API (chat.py)
    ├─ Query analysis context
    ├─ Call OpenAI with context
    └─ Return chat response
```

---

## 📊 Agent Design Pattern

Every agent follows this identical pattern:

```python
from __future__ import annotations
import pandas as pd
from loguru import logger

class SpecificAgent:
    """
    One clear responsibility: [what it does]
    
    Does NOT: [what it doesn't do]
    Uses: SpecificService for core logic
    """
    
    def process(self, df: pd.DataFrame, input_: SpecificInput) -> SpecificOutput:
        # 1. Log entry with job_id for tracing
        logger.info(f"[{input_.job_id[:8]}] SpecificAgent running")
        
        try:
            # 2. Delegate to service (core logic)
            service = SpecificService()
            result_dict = service.execute(df)
            
            # 3. Convert to typed Pydantic output
            output = SpecificOutput(
                job_id=input_.job_id,
                field1=result_dict["field1"],
                field2=result_dict["field2"],
                # ...
            )
            
            # 4. Log completion
            logger.info(f"[{input_.job_id[:8]}] Complete: summary")
            return output
            
        except Exception as e:
            # 5. Log and re-raise
            logger.error(f"[{input_.job_id[:8]}] Failed: {e}")
            raise
```

### Pattern Characteristics
- ✅ **Single Responsibility**: One job only
- ✅ **Type Safe**: Pydantic input/output models
- ✅ **Traceable**: job_id in every log
- ✅ **Testable**: Isolated from framework
- ✅ **Reusable**: Services are framework-agnostic
- ✅ **Error Handling**: Explicit error handling
- ✅ **Immutable Context**: PipelineContext passed forward

---

## 🔐 Security Architecture

### Authentication Flow
```
1. User submits credentials
   └─ POST /api/v1/auth/login

2. Backend validates
   ├─ Query User from database
   ├─ Hash password with bcrypt
   ├─ Compare hashes
   └─ On success: generate JWT token

3. JWT Token Structure
   ├─ Header: {"alg": "HS256", "typ": "JWT"}
   ├─ Payload: {"sub": user_id, "exp": expiry}
   └─ Signature: HMAC(secret)

4. Client stores token in localStorage
   └─ httpOnly=False (for SPA access)

5. Client includes token in requests
   └─ Authorization: Bearer <token>

6. Backend validates token
   ├─ Verify signature with secret
   ├─ Check expiry
   ├─ Extract user_id
   └─ On success: inject user into request
```

### Data Security
- **Passwords**: Hashed with bcrypt (12 rounds)
- **API Keys**: Stored in `.env` (never in code)
- **Database**: Connection pooling + SQL injection prevention
- **File Upload**: Size validation + virus scan ready
- **CORS**: Configured to allow frontend origin
- **HTTPS**: Ready for production (configure Nginx)

### Database Security
```sql
-- Users table (encrypted password)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,  -- bcrypt hash
    email VARCHAR,
    is_active BOOLEAN DEFAULT TRUE
);

-- Datasets: owned by user
CREATE TABLE datasets (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    filename VARCHAR,
    file_path VARCHAR,  -- local path, never exposed
    upload_time TIMESTAMP
);

-- Analysis jobs: track execution
CREATE TABLE analysis_jobs (
    id UUID PRIMARY KEY,
    dataset_id UUID REFERENCES datasets(id),
    user_id UUID REFERENCES users(id),
    status ENUM('pending', 'running', 'completed', 'failed'),
    current_stage VARCHAR,
    progress INTEGER (0-100),
    error_message VARCHAR
);
```

---

## 📊 Data Model

### Entity Relationships

```
User (1)
  │
  ├──────┬─────────────────┐
  │      │                 │
  ▼      ▼                 ▼
Dataset  AnalysisJob    (future: Subscription)
         │
         ├──────────┬──────────┬──────────┬─────────┐
         │          │          │          │         │
         ▼          ▼          ▼          ▼         ▼
    AnalysisResult  Chart    MLModel    Report   (future: Event)
```

### Core Tables

```
AnalysisJob
├─ id: UUID (primary key)
├─ dataset_id: UUID (foreign key)
├─ user_id: UUID (foreign key)
├─ status: ENUM (pending, running, completed, failed)
├─ current_stage: VARCHAR (planning, profiling, cleaning, ...)
├─ progress: INTEGER (0-100)
├─ started_at: TIMESTAMP
├─ completed_at: TIMESTAMP
├─ error_message: VARCHAR (nullable)
└─ created_at: TIMESTAMP

AnalysisResult (polymorphic per result_type)
├─ id: UUID (primary key)
├─ job_id: UUID (foreign key)
├─ result_type: VARCHAR (planner, profile, cleaning, eda, findings, ...)
├─ data: JSONB (flexible schema per stage)
└─ created_at: TIMESTAMP

Chart
├─ id: UUID (primary key)
├─ job_id: UUID (foreign key)
├─ title: VARCHAR
├─ chart_type: VARCHAR (histogram, boxplot, heatmap, ...)
├─ plotly_json: JSONB (complete Plotly figure)
└─ created_at: TIMESTAMP

MLModel
├─ id: UUID (primary key)
├─ job_id: UUID (foreign key)
├─ model_name: VARCHAR (Logistic Regression, Random Forest, ...)
├─ task_type: VARCHAR (classification, regression)
├─ metrics: JSONB ({"accuracy": 0.92, "f1": 0.89, ...})
├─ feature_importance: JSONB ({feature: importance, ...})
├─ is_best: BOOLEAN
└─ created_at: TIMESTAMP

Report
├─ id: UUID (primary key)
├─ job_id: UUID (foreign key)
├─ pdf_path: VARCHAR (file system path)
├─ executive_summary: TEXT
├─ business_insights: TEXT
└─ created_at: TIMESTAMP
```

---

## 🧠 Decision Log

### 1. Single Responsibility per Agent
**Decision**: Each agent does ONE thing only
**Rationale**:
- Easier to test independently
- Easier to debug (isolate failures)
- Easier to replace/upgrade individual stages
- Matches Unix philosophy
- Improves readability

### 2. Type-Safe I/O with Pydantic
**Decision**: All agent I/O via Pydantic models
**Rationale**:
- Catches type errors at validation time
- Auto-generates API docs
- Serializable to JSON
- Enables static type checking

### 3. Immutable PipelineContext
**Decision**: Context passed immutably through agents
**Rationale**:
- Prevents accidental data corruption
- Thread-safe (ready for future async)
- Enables easy rollback
- Clear data flow

### 4. Services not Reimplemented
**Decision**: Agents wrap services, don't reimplement
**Rationale**:
- Preserves existing tested logic
- Single source of truth
- Easier maintenance
- Follows DRY principle

### 5. Celery for Background Tasks
**Decision**: Pipeline runs as background task
**Rationale**:
- Frontend doesn't block on analysis
- Can scale with worker pool
- Enables long-running analyses
- Production-ready

---

## ⚡ Performance Considerations

### Current (Development)
- **Database**: SQLite (single-file, good for dev)
- **Task Queue**: Synchronous in-process (good for dev)
- **Caching**: None (small datasets)
- **Scaling**: Single worker

### Recommended (Production)
- **Database**: PostgreSQL (connection pooling, scaling)
- **Task Queue**: Redis + Celery workers (distributed)
- **Caching**: Redis (result caching)
- **Scaling**: Multiple workers, load balancer

### Optimization Opportunities
1. **Model Training**: Parallel training (one worker per model)
2. **Chart Generation**: Lazy loading (on-demand charts)
3. **PDF Generation**: Async PDF rendering
4. **Database**: Batch inserts for charts
5. **API**: Cache GET endpoints with Redis

---

## 🐳 Deployment Architecture (Phase 2)

```
Internet
   │
   ▼
┌─────────────────────────────────────────────────┐
│          Nginx Reverse Proxy                    │
│  ├─ Port 80 → 443 (HTTPS redirect)             │
│  ├─ Load balance across backend instances      │
│  ├─ Serve static frontend files                │
│  └─ Cache static assets (1 year)               │
└──────┬──────────────────────────────────────────┘
       │
       ├────────────────────┬────────────────────┐
       │                    │                    │
       ▼                    ▼                    ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Backend 1  │      │  Backend 2  │      │  Backend N  │
│  (FastAPI)  │      │  (FastAPI)  │      │  (FastAPI)  │
├─────────────┤      ├─────────────┤      ├─────────────┤
│ 8 Agents    │      │ 8 Agents    │      │ 8 Agents    │
│ Services    │      │ Services    │      │ Services    │
│ Routes      │      │ Routes      │      │ Routes      │
└──────┬──────┘      └──────┬──────┘      └──────┬──────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
                ▼           ▼           ▼
         ┌──────────────────────────────────┐
         │    PostgreSQL Database           │
         │  (Replicated for HA)             │
         │  (Automated backups)             │
         └──────────────────────────────────┘
         
         ┌──────────────────────────────────┐
         │    Redis (Session + Cache)       │
         │  (Replicated for HA)             │
         └──────────────────────────────────┘
         
         ┌──────────────────────────────────┐
         │ Celery Workers (N instances)     │
         │  • Model training (GPU optional) │
         │  • PDF generation                │
         │  • AI inference (OpenAI batch)   │
         └──────────────────────────────────┘
         
         ┌──────────────────────────────────┐
         │ File Storage (S3 compatible)     │
         │  • Uploaded datasets             │
         │  • Generated PDFs                │
         │  • Backup storage                │
         └──────────────────────────────────┘
```

---

## 📈 Monitoring & Observability

### Logging Strategy
```
All logs include:
- [job_id[:8]]  - 8-char job identifier (for filtering)
- [stage]       - Current pipeline stage
- [timestamp]   - ISO 8601 format
- [level]       - DEBUG, INFO, WARNING, ERROR
- [message]     - Structured log message

Example:
[abc12345] [planning] [2024-01-15T10:30:45Z] [INFO] PlannerAgent detected classification task
```

### Metrics to Track
- ✅ Pipeline success rate
- ✅ Average pipeline duration
- ✅ Per-stage duration
- ✅ Model training duration
- ✅ PDF generation duration
- ✅ API response times
- ✅ Database query times
- ✅ Celery task queue length

### Health Checks
```bash
# Endpoint
GET /health

# Response
{
  "status": "healthy",
  "database": "connected",
  "cache": "connected",
  "openai": "reachable",
  "uptime": 3600
}
```

---

## 🎓 Extension Points

### Adding a New Agent

1. **Define I/O Schema** (`agents/schemas.py`)
   ```python
   class NewAgentInput(BaseModel):
       job_id: str
       # ... other fields
   
   class NewAgentOutput(BaseModel):
       job_id: str
       # ... output fields
   ```

2. **Implement Agent** (`agents/new_agent.py`)
   ```python
   class NewAgent:
       def process(self, df: pd.DataFrame, input_: NewAgentInput) -> NewAgentOutput:
           service = NewService()
           result = service.execute(df)
           return NewAgentOutput(...)
   ```

3. **Create Service** (`services/new_service.py`)
   ```python
   class NewService:
       def execute(self, df: pd.DataFrame) -> dict:
           # Core logic here
           return {...}
   ```

4. **Add to Pipeline** (`tasks/pipeline.py`)
   ```python
   new_agent = NewAgent()
   new_input = NewAgentInput(job_id=job_id)
   new_output = new_agent.process(df, new_input)
   _save_result(db, job_id, "new_agent", new_output.model_dump())
   ```

5. **Export Agent** (`agents/__init__.py`)
   ```python
   from .new_agent import NewAgent
   __all__ = [..., "NewAgent"]
   ```

### Adding a New API Endpoint

1. **Create route** (`api/v1/endpoints/new.py`)
   ```python
   router = APIRouter()
   
   @router.post("/new")
   async def create_new(request: NewRequest, user: User = Depends(get_current_user)):
       # API logic here
       return {"result": ...}
   ```

2. **Register router** (`api/v1/router.py`)
   ```python
   from endpoints.new import router
   api_router.include_router(router, prefix="/new")
   ```

---

## 📚 References

- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://www.sqlalchemy.org/
- **Pydantic**: https://docs.pydantic.dev/
- **Celery**: https://docs.celeryproject.io/
- **Next.js**: https://nextjs.org/
- **Plotly**: https://plotly.com/
- **Scikit-learn**: https://scikit-learn.org/
- **XGBoost**: https://xgboost.readthedocs.io/

---

**Architecture v1.0** | Last Updated: 2026-08-09
