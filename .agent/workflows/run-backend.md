---
description: Start the FastAPI backend server for local development
---

# Run Backend

## Prerequisites
- Python virtual environment activated
- Dependencies installed from `backend/requirements.txt`

## Steps

1. Activate the virtual environment:
```bash
source venv/bin/activate
```

// turbo
2. Start the FastAPI server with hot reload:
```bash
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Expected Output
- Server running at `http://localhost:8000`
- API docs available at `http://localhost:8000/docs`
