# Software Requirements Specification (SRS) for SupplyShield

## 1. Introduction

### 1.1 Purpose
The purpose of this document is to define the Software Requirements Specification for **SupplyShield**. This document outlines the system's AI-driven capabilities, overarching decoupled architecture, and the functional endpoints used to design, run, and evaluate the supply chain risk platform.

### 1.2 Scope
SupplyShield is an **AI-Powered Supply Chain Risk Intelligence & Inventory Orchestration** application. It serves to ingest unorganized supply chain data (`.csv` / `.xlsx`) and output predictive risk modeling. It covers supplier failure heuristics via machine learning, visual 90-day time-series stock forecasting using Facebook Prophet, and BOM redundancy matching using FAISS vector similarity search.

### 1.3 Tech Stack Summary
- **Frontend OS**: React 19 running on Vite Builder.
- **Frontend Libraries**: `@supabase/supabase-js` (Auth), `recharts` (Forecasting Charts), `lucide-react` (SVG Icons), `react-router-dom` (Navigation).
- **Backend API**: Python 3.10+ via FastAPI, mounted on `uvicorn`.
- **Backend ML & Data Processing**: `prophet` (Time-series), `faiss-cpu` (Vector Matrix Matching), `scikit-learn` & `huggingface_hub` (Heuristics), `pandas` & `numpy` (DF transformation).
- **ORM & Database**: `SQLAlchemy` mapping directly into Supabase (PostgreSQL).

### 1.4 Definitions and Acronyms
- **BOM (`bom_routes.py`)**: Bill of Materials. Describes the hierarchical blueprint of components evaluated during upload mapping. 
- **FAISS**: Facebook AI Similarity Search.
- **Prophet**: Additive regression model generating future interval margins (`yhat`, `yhat_lower`, `yhat_upper`).
- **Supabase**: Backend-as-a-Service providing PostgreSQL and row-level JWT user authentication.

---

## 2. Overall Description

### 2.1 Product Description
The application operates as a distributed web infrastructure. Procurement leaders and engineers upload component CSVs, which are digested into PostgreSQL schemas. The user can then query risk algorithms to cross-reference current inventory against expected delivery margins to flag potential stockout dates.

### 2.2 Architecture Overview
The system follows a strict **Decoupled Client-Server Monolithic API Architecture**:
- **Client**: A robust Single Page Application (SPA) driven by React handling complex layout charting and user interactions on local browser memory.
- **Server**: A stateless Python FastAPI monolith implementing isolated Controller routing (`api/`) mapped to Service processing (`services/`).
- **Database**: Supabase cloud handles all definitive state storage.

### 2.3 User Roles
- **Authenticated Manager**: Assumed from the `user_routes.py` logic which binds generic user states to protected data fetching scopes via token validation (`getAccessToken`).

### 2.4 Key Dependencies Found
- **`package.json`**: `react`, `recharts`, `@supabase/supabase-js`, `lucide-react`.
- **`requirements.txt`**: `fastapi`, `prophet`, `faiss-cpu`, `scikit-learn`, `SQLAlchemy`, `pandas`, `huggingface_hub`, `python-jose` (used for JWT parsing).

---

## 3. Functional Requirements

### Internal Dashboard
- **REQ-F-001 | Fetch Summary Stats |** The system must compute aggregated dashboard statistics (component counts, supplier lists) and return them via GET. **File Ref**: `dashboard_router.py` | **Priority**: High

### Setup & Onboarding
- **REQ-F-002 | Upload Component Files |** The system must accept `multipart/form-data` payloads of inventory and component specification data for database population. **File Ref**: `setup_routes.py` (`/upload-all`, `/inventory`, `/components`) | **Priority**: Critical
- **REQ-F-003 | Build Vector Indexes |** The system must utilize the FAISS-CPU library to embed components into a searchable vector index upon receiving a POST command. **File Ref**: `setup_routes.py` (`/build-indexes`) | **Priority**: High

### BOM Analysis
- **REQ-F-004 | Target Alternative Supplies |** The system must digest User BOM & Receipt files concurrently, and calculate the Euclidean distance to find compatible alternative inventory choices. **File Ref**: `bom_routes.py` (`/bom`) | **Priority**: High

### Machine Learning Risk Engines
- **REQ-F-005 | Neural Supplier Risk Check |** The system must evaluate external model heuristics to output a `RiskPredictionResponse` dictating entity reliability via external model inferences. **File Ref**: `risk_routes.py` (`/predict-all`) | **Priority**: High
- **REQ-F-006 | Train Prophet Pipeline |** The system must process chronological time-series stock arrays dynamically against Facebook's Prophet framework, generating a 90-day trajectory. **File Ref**: `internal_risk_routes.py` (`/run-prophet`) | **Priority**: Critical
- **REQ-F-007 | Fetch Single Forecast Range |** The UI must be able to securely isolate one specific `component_id` and fetch its associated generated `stockout_date` chart. **File Ref**: `internal_risk_routes.py` (`/forecast/{component_id}`) | **Priority**: High

---

## 4. Non-Functional Requirements

- **REQ-NF-001 | Performance |** Visual rendering of Prophet prediction matrices must be handled efficiently over the HTML canvas or SVG layer using `recharts` to prevent DOM blockages. *(Evidence: Usage of Vite bundler optimization and `recharts` library dependencies)*
- **REQ-NF-002 | Security Authorization |** API requests mapping private vendor intelligence must carry Secure Bearer authorization tokens natively evaluated against Supabase scopes. *(Evidence: Usage of `getAccessToken()` internally via `api.js` before POST requests)*
- **REQ-NF-003 | Reliability |** Time-series evaluations against Prophet require robust Python `try/catch` fallbacks, as forecasting components with less than 5 rows of `received_date` history will inevitably crash the model algorithms. *(Evidence: Guard clauses found inside `internal_risk_service.py` requiring historical parameters)*

---

## 5. API & Interface Requirements

### Identified Endpoint Controllers:
**User Module (`user_routes.py`)**
- `POST /api/users/profile` - Create Auth profile mapping.
- `GET /api/users/profile` - Validates and fetches Auth mapping.

**Setup Module (`setup_routes.py`)**
- `POST /api/setup/components`
- `POST /api/setup/component-specs`
- `POST /api/setup/suppliers`
- `POST /api/setup/supplier-components`
- `POST /api/setup/inventory`
- `POST /api/setup/projects`
- `POST /api/setup/build-indexes`
- `GET /api/setup/status`

**Dashboard Analytics (`dashboard_router.py`)**
- `GET /api/dashboard/summary`
- `GET /api/dashboard/components`
- `GET /api/dashboard/suppliers`
- `GET /api/dashboard/inventory`

**BOM Evaluation (`bom_routes.py`)**
- `POST /api/analysis/bom`

**Supplier Risk AI (`risk_routes.py`)**
- `POST /api/supplier-risk/predict`
- `POST /api/supplier-risk/predict-all`

**Inventory Threat Prediction (`internal_risk_routes.py`)**
- `POST /api/risk/run-prophet`
- `GET /api/risk/predictions`
- `GET /api/risk/predictions/{component_id}`
- `GET /api/risk/summary`
- `GET /api/risk/forecast/{component_id}`

---

## 6. Data Flow

1. **Ingestion & Hydration**: End-users drag and drop Excel/CSV manifests matching Supplier info, Component Specifications, and Inventory states natively within the React UI view (`InventoryRisk.jsx`, `api.js`). We execute multipart submissions sequentially targeting the `setup_routes.py`.
2. **Indexing**: Background processes construct flat indexes inside FAISS taking string semantics and rendering them calculable for AI mapping.
3. **Execution Routing**: When a user queries `Train Prophet`, the frontend calls `/api/risk/run-prophet`, locking the execution thread while pandas aggregates local PostgreSQL history datasets and `prophet` renders a multi-day calculation loop.
4. **Presentation Output**: Raw datasets (JSON intervals bounded by `yhat_lower`/`upper`) are fed back asynchronously, mapped onto `Recharts` responsive `ProphetChart` components inside React, mapping thresholds over physical safety-stock visual reference lines.

---

## 7. Appendix

### 7.1 Glossary
- **`ProphetChart.jsx`**: Custom React context wrapping the Recharts API to render `yhat` projections.
- **Euclidean Distance**: Vector metric mapping how closely related two disparate component IDs are inside FAISS dimensions.
- **Heuristics**: Model-based algorithmic shortcuts identifying bad vendors.

### 7.2 Files Scanned Automatically
* `backend/requirements.txt`
* `frontend/package.json`
* `frontend/src/services/api.js`
* `backend/api/dashboard_router.py`
* `backend/api/user_routes.py`
* `backend/api/bom_routes.py`
* `backend/api/setup_routes.py`
* `backend/api/risk_routes.py`
* `backend/api/internal_risk_routes.py`
* `frontend/src/pages/InventoryRisk.jsx`

### 7.3 Items Marked [TO BE DEFINED] 
- **[TO BE DEFINED]:** Explicit deployment architecture schema (e.g., Docker container constraints, CI/CD pipeline routing, AWS/Vercel platform decisions).
- **[TO BE DEFINED]:** Supabase internal table RLS schema layouts.
