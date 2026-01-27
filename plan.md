# Deployment Guide Plan

## 1. Containerization
- Create `backend/Dockerfile`: Optimized Python 3.11-slim image.
- Create `frontend/Dockerfile`: Multi-stage build (Node -> Nginx) to serve the Vue.js app.

## 2. Environment Variables
- Refactor `backend/app/main.py` to use `os.getenv` for:
    - `CORS_ALLOWED_ORIGINS`
    - `TASK_CLEANUP_MAX_AGE`
    - `TASK_CLEANUP_INTERVAL`
    - `PORT` (for Cloud Run compatibility)

## 3. Documentation (deployment_guide.md)
- **Cloud Run**:
    - Build and Push commands.
    - Deploy command with environment variables.
    - Scaling (concurrency settings).
- **GKE**:
    - Kubernetes manifests (Deployment, Service, HPA).
    - Horizontal Scaling Caveat: **Sticky Sessions** requirement due to in-memory task registry.
- **Monitoring Integration**:
    - Instructions for scraping the `/metrics` endpoint in a production K8s cluster.

## 4. Verification
- Verify Docker builds locally.