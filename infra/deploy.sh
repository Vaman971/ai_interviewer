#!/usr/bin/env bash
# =============================================================================
# deploy.sh — AI Interviewer full AWS deployment script (macOS / Linux)
# Usage: bash infra/deploy.sh
# =============================================================================

set -euo pipefail   # exit on error, unset vars, or pipe failures

# ── Resolve project root (parent of infra/ regardless of where you run from) ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; RED='\033[0;31m'; NC='\033[0m'

# ── STEP 0: Verify tools are available ───────────────────────────────────────
echo -e "\n${CYAN}[0/7] Checking prerequisites...${NC}"
for tool in aws terraform kubectl docker; do
    if ! command -v "$tool" &>/dev/null; then
        echo -e "${RED}ERROR: '$tool' not found. Please install it and try again.${NC}" >&2
        exit 1
    fi
done
echo -e "${GREEN}  All tools present.${NC}"

# ── STEP 1: Terraform apply (create AWS infrastructure) ──────────────────────
echo -e "\n${CYAN}[1/7] Running terraform apply...${NC}"
cd "$ROOT/infra/terraform"
terraform init -upgrade
terraform apply -auto-approve || { echo -e "${RED}terraform apply failed${NC}" >&2; exit 1; }

# Read outputs
ACCOUNT_ID=$(terraform output -raw aws_account_id)
ECR_BACKEND=$(terraform output -raw ecr_backend_url)
ECR_FRONTEND=$(terraform output -raw ecr_frontend_url)
CLUSTER_NAME=$(terraform output -raw eks_cluster_name)
RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
REDIS_ENDPOINT=$(terraform output -raw redis_endpoint)
AWS_REGION=$(terraform output -raw aws_region 2>/dev/null || echo "us-east-1")

echo -e "${GREEN}  ECR Backend:  $ECR_BACKEND${NC}"
echo -e "${GREEN}  ECR Frontend: $ECR_FRONTEND${NC}"
echo -e "${GREEN}  EKS Cluster:  $CLUSTER_NAME${NC}"

# ── STEP 2: Authenticate Docker to ECR ───────────────────────────────────────
echo -e "\n${CYAN}[2/7] Logging Docker into ECR...${NC}"
aws ecr get-login-password --region "$AWS_REGION" \
    | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com" \
    || { echo -e "${RED}ECR login failed${NC}" >&2; exit 1; }

# ── STEP 3: Build and push Docker images ─────────────────────────────────────
echo -e "\n${CYAN}[3/7] Building and pushing Docker images...${NC}"
cd "$ROOT"

docker build -f infra/docker/Dockerfile.backend  -t "${ECR_BACKEND}:latest"  . \
    || { echo -e "${RED}Backend Docker build failed${NC}" >&2; exit 1; }
docker push "${ECR_BACKEND}:latest"

docker build -f infra/docker/Dockerfile.frontend -t "${ECR_FRONTEND}:latest" . \
    || { echo -e "${RED}Frontend Docker build failed${NC}" >&2; exit 1; }
docker push "${ECR_FRONTEND}:latest"

echo -e "${GREEN}  Images pushed to ECR.${NC}"

# ── STEP 4: Configure kubectl to talk to EKS ─────────────────────────────────
echo -e "\n${CYAN}[4/7] Configuring kubectl for EKS...${NC}"
aws eks update-kubeconfig --name "$CLUSTER_NAME" --region "$AWS_REGION" \
    || { echo -e "${RED}kubectl config failed${NC}" >&2; exit 1; }

# ── STEP 5: Create K8s Secrets and ConfigMap ─────────────────────────────────
echo -e "\n${CYAN}[5/7] Creating K8s secrets and ConfigMap...${NC}"

# Load .env file key=value pairs (ignores comments and blank lines)
ENV_FILE="$ROOT/.env"
declare -A ENV_VARS
while IFS='=' read -r key value; do
    [[ "$key" =~ ^#|^$ ]] && continue
    key="${key// /}"          # trim spaces
    value="${value//$'\r'/}" # strip Windows CR if any
    ENV_VARS["$key"]="$value"
done < <(grep -v '^\s*#' "$ENV_FILE" | grep '=')

DB_PASSWORD="${ENV_VARS[DB_PASSWORD]:-}"
if [[ -z "$DB_PASSWORD" ]]; then
    read -rsp "Enter the PostgreSQL password you chose: " DB_PASSWORD
    echo
fi

DB_USER="${ENV_VARS[db_username]:-ai_interviewer_admin}"
DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${RDS_ENDPOINT}/ai_interviewer"
REDIS_URL="redis://${REDIS_ENDPOINT}:6379/0"

# Create ConfigMap (non-sensitive values)
kubectl create configmap ai-interviewer-config \
    --from-literal=APP_ENV=production \
    --from-literal=DEBUG=false \
    --from-literal=PYTHONPATH=/app \
    --from-literal=LLM_BASE_URL="${ENV_VARS[LLM_BASE_URL]:-}" \
    --from-literal=OPENAI_MODEL="${ENV_VARS[OPENAI_MODEL]:-gpt-4o-mini}" \
    --from-literal=UPLOAD_DIR=/app/uploads \
    --from-literal=JWT_ALGORITHM=HS256 \
    --from-literal=JWT_EXPIRATION_MINUTES=1440 \
    --from-literal=NEXT_PUBLIC_API_URL="http://backend-service:80" \
    --dry-run=client -o yaml | kubectl apply -f -

# Create Secret (sensitive values)
kubectl create secret generic ai-interviewer-secrets \
    --from-literal=SECRET_KEY="${ENV_VARS[SECRET_KEY]:-}" \
    --from-literal=JWT_SECRET="${ENV_VARS[JWT_SECRET]:-}" \
    --from-literal=DATABASE_URL="$DATABASE_URL" \
    --from-literal=REDIS_URL="$REDIS_URL" \
    --from-literal=OPENAI_API_KEY="${ENV_VARS[OPENAI_API_KEY]:-}" \
    --from-literal=DEEPGRAM_API_KEY="${ENV_VARS[DEEPGRAM_API_KEY]:-}" \
    --from-literal=TAVUS_API_KEY="${ENV_VARS[TAVUS_API_KEY]:-}" \
    --dry-run=client -o yaml | kubectl apply -f -

# ── STEP 6: Patch image URLs and apply K8s manifests ─────────────────────────
echo -e "\n${CYAN}[6/7] Deploying to Kubernetes...${NC}"

sed "s|PLACEHOLDER_ECR_BACKEND_URL|${ECR_BACKEND}|g"  "$ROOT/infra/k8s/backend.yaml"  | kubectl apply -f -
sed "s|PLACEHOLDER_ECR_FRONTEND_URL|${ECR_FRONTEND}|g" "$ROOT/infra/k8s/frontend.yaml" | kubectl apply -f -

# Expose services as LoadBalancer (no ALB controller needed)
kubectl expose deployment ai-interviewer-frontend \
    --name=frontend-service --port=80 --target-port=3000 --type=LoadBalancer \
    --dry-run=client -o yaml | kubectl apply -f - 2>/dev/null || true

kubectl expose deployment ai-interviewer-backend \
    --name=backend-service --port=80 --target-port=8000 --type=LoadBalancer \
    --dry-run=client -o yaml | kubectl apply -f - 2>/dev/null || true

kubectl apply -f "$ROOT/infra/k8s/database.yaml"

# Wait for backend pod to be ready and initialize the database schema
echo -e "\n${CYAN}  Waiting for backend pod to initialize the database...${NC}"
kubectl wait --for=condition=Ready pod -l app=backend --timeout=90s
POD_NAME=$(kubectl get pods -l app=backend -o jsonpath="{.items[0].metadata.name}")
kubectl exec "$POD_NAME" -- python -c "import asyncio; import backend.app.main; from backend.app.db.database import create_tables; asyncio.run(create_tables())"
echo -e "${GREEN}  Database initialized successfully.${NC}"

# ── STEP 7: Wait and print access URLs ───────────────────────────────────────
echo -e "\n${CYAN}[7/7] Waiting for LoadBalancers to become ready (up to 3 min)...${NC}"
TRIES=0
FE_HOST=""
BE_HOST=""
while [[ ( -z "$FE_HOST" || -z "$BE_HOST" ) && $TRIES -lt 12 ]]; do
    sleep 15
    TRIES=$((TRIES + 1))
    FE_HOST=$(kubectl get svc frontend-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)
    BE_HOST=$(kubectl get svc backend-service  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)
    echo "  Attempt $TRIES/12 — Frontend: ${FE_HOST:-pending} | Backend: ${BE_HOST:-pending}"
done

echo ""
if [[ -n "$FE_HOST" ]]; then
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}  DEPLOYMENT COMPLETE!${NC}"
    echo -e "${YELLOW}  Frontend : http://${FE_HOST}${NC}"
    echo -e "${YELLOW}  API URL  : http://${BE_HOST}${NC}"
    echo -e "${CYAN}  API Docs : http://${BE_HOST}/docs${NC}"
    echo -e "${GREEN}============================================================${NC}"
else
    echo -e "${YELLOW}  LoadBalancers not ready yet — run: kubectl get svc${NC}"
fi

echo ""
echo -e "${RED}  REMEMBER: Run 'cd infra/terraform && terraform destroy -auto-approve' to delete all AWS resources!${NC}"
