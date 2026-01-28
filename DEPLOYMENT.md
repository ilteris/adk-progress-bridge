# Deployment Guide: ADK Progress Bridge

This guide provides instructions for deploying the ADK Progress Bridge to Google Cloud Platform (GCP) using **Cloud Run** (for simplicity and serverless scaling) or **GKE Autopilot** (for robust, cluster-based orchestration).

---

## 🏗️ Prerequisites

1.  **GCP Project**: A Google Cloud Project with billing enabled.
2.  **Google Cloud CLI**: Installed and authenticated (`gcloud auth login`).
3.  **Docker**: Installed locally for building and pushing images.
4.  **APIs Enabled**:
    ```bash
    gcloud services enable \
        artifactregistry.googleapis.com \
        run.googleapis.com \
        container.googleapis.com \
        monitoring.googleapis.com
    ```

---

## 📦 1. Artifact Registry Setup

Create a Docker repository to store your backend and frontend images.

```bash
# Set your variables
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1
export REPO_NAME=adk-bridge-repo

# Create the repository
gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="Docker repository for ADK Progress Bridge"

# Authenticate Docker to the registry
gcloud auth configure-docker $REGION-docker.pkg.dev
```

---

## 🚀 2. Option A: Deploy to Cloud Run (Recommended)

Cloud Run is ideal for this application as it handles request-based scaling and supports Server-Sent Events (SSE) natively.

### Step 1: Build and Push Images

```bash
# Build & Push Backend
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/backend:latest ./backend
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/backend:latest

# Build & Push Frontend (Note: VITE_API_URL must be the final backend URL)
# For the first deployment, you might need to deploy the backend first to get its URL.
docker build --build-arg VITE_API_URL=https://backend-url.a.run.app \
    -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/frontend:latest ./frontend
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/frontend:latest
```

### Step 2: Deploy Backend

```bash
gcloud run deploy adk-backend \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/backend:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars="CORS_ALLOWED_ORIGINS=*" \
    --timeout=3600
```
*Note: The `--timeout` is set to 1 hour to accommodate long-running tools.*

### Step 3: Deploy Frontend

```bash
gcloud run deploy adk-frontend \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/frontend:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated
```

---

## ☸️ 3. Option B: Deploy to GKE Autopilot

GKE Autopilot provides a fully managed Kubernetes experience, suitable for complex scaling needs or integration with existing K8s workloads.

### Step 1: Create Cluster

```bash
gcloud container clusters create-auto adk-bridge-cluster \
    --region $REGION \
    --release-channel regular
```

### Step 2: Prepare Manifests

Create a `k8s-deploy.yaml` file (replacing placeholders with your values):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: adk-backend
spec:
  selector:
    matchLabels:
      app: adk-backend
  template:
    metadata:
      labels:
        app: adk-backend
    spec:
      containers:
      - name: backend
        image: REGION-docker.pkg.dev/PROJECT_ID/REPO_NAME/backend:latest
        ports:
        - containerPort: 8080
        env:
        - name: CORS_ALLOWED_ORIGINS
          value: "*"
---
apiVersion: v1
kind: Service
metadata:
  name: adk-backend-svc
spec:
  selector:
    app: adk-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

### Step 3: Deploy to Cluster

```bash
gcloud container clusters get-credentials adk-bridge-cluster --region $REGION
kubectl apply -f k8s-deploy.yaml
```

---

## 📊 4. Observability & Monitoring

The backend exposes Prometheus metrics at `/metrics`.

### GKE: Managed Service for Prometheus
GKE Autopilot has Managed Service for Prometheus enabled by default. To scrape metrics, apply a `PodMonitoring` resource:

```yaml
apiVersion: monitoring.googleapis.com/v1
kind: PodMonitoring
metadata:
  name: adk-backend-monitoring
spec:
  selector:
    matchLabels:
      app: adk-backend
  endpoints:
  - port: 8080
    path: /metrics
    interval: 30s
```

### Cloud Run: Cloud Monitoring
For Cloud Run, metrics can be collected using the [OpenTelemetry Sidecar](https://cloud.google.com/stackdriver/docs/solutions/opentelemetry/cloud-run) or by configuring a custom scraper.

---

## 🔐 Security & Best Practices

5.  **WebSocket Support**: If using a Load Balancer or Ingress (especially on GKE or Cloud Run), ensure that WebSocket support is enabled and that connection timeouts are configured appropriately (e.g., 3600s) to prevent the socket from being closed prematurely. Most modern GCP services handle WebSockets automatically, but custom Ingress controllers may require specific annotations (e.g., `nginx.org/websocket-services`).

1.  **CORS**: In production, replace `CORS_ALLOWED_ORIGINS=*` with the actual domain of your frontend.
2.  **Timeouts**: Ensure your Load Balancers or Ingress controllers have high timeouts (e.g., 600s+) to prevent premature closure of the SSE stream.
3.  **Secret Manager**: Use [Google Secret Manager](https://cloud.google.com/secret-manager) for sensitive environment variables like API keys.
4.  **IAP**: For internal tools, consider using **Identity-Aware Proxy (IAP)** to restrict access to authorized users only.

---

## 🛠️ Local Development (Quick Start)

If you just want to run the whole stack locally using Docker Compose:

```bash
docker-compose up --build
```
The frontend will be available at `http://localhost:5173` and the backend at `http://localhost:8080`.