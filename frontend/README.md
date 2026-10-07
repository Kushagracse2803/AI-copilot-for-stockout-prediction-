# Om Traders — Frontend

React (Vite) frontend for the stockout risk copilot.

## Setup

```bash
npm install
npm run dev
```

Opens at http://localhost:5173

## Requires

- The FastAPI backend running on http://127.0.0.1:8000 (`uvicorn api.main:app --reload --app-dir src`, from the project root)
- Two additions to `src/api/main.py`: the CORS middleware and the `/products` endpoint (see project chat/notes)
