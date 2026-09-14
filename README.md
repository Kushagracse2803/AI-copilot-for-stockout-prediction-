# CPG Stockout Risk & Replenishment Copilot

An AI copilot that predicts SKU-location stockout risk for the next 7–14 days and
gives planners evidence-based, human-approved replenishment recommendations.

> Example output the system is designed to produce:
> *"Mumbai DC may run out of 500g detergent in nine days. Recommended action:
> transfer 1,200 units from Pune DC and order 2,500 units from Supplier B.
> Evidence: forecast uplift of 18%, current inventory coverage of 6.2 days,
> and an approved minimum safety stock of 900 units."*

## Why this project exists

Regional warehouses and stores frequently stock out even though demand
forecasts already exist. The gap isn't forecasting — it's **explainability
and action**: planners don't have time to dig through dashboards to
understand *why* a shortage is likely or *what exactly* to do about it. This
system closes that gap while keeping every action auditable and
human-approved — **the system never places an order on its own.**

## Architecture — the seven pieces

```
                     ┌─────────────────────┐
  Sales, inventory,  │  1. ML PREDICTION    │  XGBoost/LightGBM → stockout-risk
  promo, pricing,    │  (src/models)        │  score per SKU-location
  lead-time data ───▶│                      │
                     └──────────┬───────────┘
                                │ risk score + feature importances
                                ▼
                     ┌──────────────────────┐
                     │  2. LLM EXPLANATION   │  Turns model output into a
                     │  (src/llm)            │  plain-English business reason
                     └──────────┬───────────┘
                                │
              ┌─────────────────┴──────────────────┐
              ▼                                     ▼
   ┌─────────────────────┐              ┌──────────────────────┐
   │  3. RAG RETRIEVAL     │              │  4. ACTION            │
   │  (src/rag)            │─────────────▶│  RECOMMENDATION        │
   │  policies, contracts,│  citations    │  (src/rules)           │
   │  safety-stock rules  │              │  qty, source, ETA,      │
   └─────────────────────┘              │  filtered by hard rules │
                                          └───────────┬─────────────┘
                                                       │ draft only
                                                       ▼
   ┌─────────────────────┐              ┌──────────────────────┐
   │  5. vLLM              │◀────────────│  6. MCP TOOLS          │
   │  (serving layer)      │  hosts the  │  (src/mcp_server)      │
   │                       │  LLM used   │  get_inventory,         │
   │                       │  above      │  create_replenishment_ │
   │                       │             │  draft (never auto-    │
   │                       │             │  approved)              │
   └─────────────────────┘              └──────────────────────┘

   All of the above is served through:
   ┌──────────────────────────────────────────────────────────────┐
   │  7. FastAPI (src/api)  →  deployed on Azure (AKS / Container  │
   │  Apps), backed by Data Lake, Azure ML, Azure AI Search,       │
   │  Key Vault, Entra ID, and Application Insights                │
   └──────────────────────────────────────────────────────────────┘
```

## Project status

| Piece | Status | Location |
|---|---|---|
| 1. ML prediction (XGBoost) | ✅ Working | `src/data_generation`, `src/features`, `src/models` |
| 7. FastAPI serving layer | ✅ Working (prediction endpoint live) | `src/api` |
| 2. LLM explanation | ⏳ Not started | `src/llm` (stub) |
| 3. RAG retrieval | ⏳ Not started | `src/rag` (stub) |
| 4. Action recommendation rules | ⏳ Not started | `src/rules` (stub) |
| 5. vLLM serving | ⏳ Not started | — |
| 6. MCP tools | ⏳ Not started | `src/mcp_server` (stub) |
| Azure deployment | ⏳ Not started | — |

## Folder structure

```
cpg-stockout-copilot/
├── README.md
├── pyproject.toml          # uv-managed dependencies (see below)
├── uv.lock                 # committed - locks exact versions for everyone
├── .env.example            # copy to .env and fill in real values
├── .gitignore
├── data/
│   ├── raw/                 # simulated/real sales+inventory data (gitignored)
│   ├── processed/           # engineered features (gitignored)
│   └── documents/           # supplier contracts, policy docs for RAG (gitignored)
├── models/                  # trained model artifacts (gitignored, use model registry)
├── notebooks/
│   └── 01_stockout_risk_prediction_walkthrough.ipynb
├── src/
│   ├── config.py            # shared paths & constants
│   ├── data_generation/     # Piece 1: synthetic data simulation
│   ├── features/            # Piece 1: feature engineering (no data leakage)
│   ├── models/               # Piece 1: train.py, evaluate.py
│   ├── llm/                  # Piece 2: prompts + explanation generation
│   ├── rag/                  # Piece 3: document ingestion + retrieval
│   ├── rules/                 # Piece 4: deterministic inventory constraints
│   ├── mcp_server/            # Piece 6: MCP tool definitions
│   └── api/                   # Piece 7: FastAPI app
│       ├── main.py
│       ├── schemas.py
│       ├── dependencies.py
│       └── routers/
└── tests/
```

## Setup

This project uses **[uv](https://docs.astral.sh/uv/)** instead of plain
`pip`/`requirements.txt`. Why: uv resolves and locks exact dependency
versions (`uv.lock`), so "works on my machine" version drift goes away, and
it separates heavy, piece-specific dependencies (vLLM, Azure SDKs,
sentence-transformers) into optional groups so a fresh clone doesn't force
everyone to download gigabytes of GPU libraries just to work on the API.

```bash
# 1. Install uv (one-time, if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install core dependencies (ML + API - lightweight, always needed)
uv sync

# 3. Install optional pieces as you work on them:
uv sync --extra rag          # sentence-transformers, chromadb, pypdf (Piece 3)
uv sync --extra azure        # Azure SDKs (Piece: deployment)
uv sync --extra serving      # vLLM (Piece 5 - large, GPU-oriented)
uv sync --extra forecasting  # Prophet, if comparing against XGBoost

# Install everything at once:
uv sync --all-extras

# 4. Copy environment variables template
cp .env.example .env   # then fill in real values
```

## Running Piece 1 — ML prediction pipeline

```bash
uv run python src/data_generation/generate_synthetic_data.py   # simulate data
uv run python src/features/build_features.py                    # engineer features
uv run python src/models/train.py                                # train XGBoost
```

Or walk through it interactively:

```bash
uv run jupyter lab notebooks/01_stockout_risk_prediction_walkthrough.ipynb
```

## Running the API (Piece 7)

```bash
uv run uvicorn api.main:app --reload --app-dir src
```

Then open **http://127.0.0.1:8000/docs** for interactive API docs.

Example:
```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/predict/SKU_000/LOC_00
```

## Success metrics

| Metric | Target |
|---|---|
| Forecast error (WAPE/MAPE) | Track & minimize |
| Stockout prediction (Precision, Recall, PR-AUC) | PR-AUC prioritized (imbalanced problem) |
| Stockout reduction | 10–15% |
| Planner acceptance rate | > 70% |
| Grounded answer rate (RAG citations) | > 90% |
| P95 response latency | < 5 seconds |
| Autonomous purchase orders | **Zero** — draft-only, always requires human approval |

## Design principles

- **No data leakage:** features only use information available as of "today";
  labels look forward — kept strictly separate throughout the pipeline.
- **Time-based splitting:** train/test splits are always by date, never random,
  to mimic real-world forecasting conditions.
- **Explainability by construction:** the LLM explanation layer is grounded in
  the ML model's own feature importances and retrieved policy documents — it
  narrates real signals, it doesn't invent reasoning.
- **Bounded autonomy:** deterministic business rules validate every
  recommendation before display; MCP's `create_replenishment_draft` tool can
  only ever create a *draft* — never a live purchase order.# AI-copilot-for-stockout-prediction-
