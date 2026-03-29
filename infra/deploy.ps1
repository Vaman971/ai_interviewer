# =============================================================================
# deploy.ps1 — AI Interviewer full AWS deployment script
# Usage: .\infra\deploy.ps1
# =============================================================================

# Refresh PATH so aws/terraform/kubectl are found
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")

$ROOT = $PSScriptRoot | Split-Path   # Project root

# ── STEP 0: Verify tools are available ───────────────────────────────────────
Write-Host "`n[0/7] Checking prerequisites..." -ForegroundColor Cyan
aws --version   | Out-Null; if ($LASTEXITCODE -ne 0) { Write-Error "AWS CLI not found"; exit 1 }
terraform --version | Out-Null; if ($LASTEXITCODE -ne 0) { Write-Error "Terraform not found"; exit 1 }
kubectl version --client | Out-Null; if ($LASTEXITCODE -ne 0) { Write-Error "kubectl not found"; exit 1 }
Write-Host "  All tools present." -ForegroundColor Green

# ── STEP 1: Terraform apply (create AWS infrastructure) ──────────────────────
Write-Host "`n[1/7] Running terraform apply..." -ForegroundColor Cyan
Set-Location "$ROOT\infra\terraform"
terraform init -upgrade
terraform apply -auto-approve
if ($LASTEXITCODE -ne 0) { Write-Error "terraform apply failed"; exit 1 }

# Read outputs
$ACCOUNT_ID    = (terraform output -raw aws_account_id)
$ECR_BACKEND   = (terraform output -raw ecr_backend_url)
$ECR_FRONTEND  = (terraform output -raw ecr_frontend_url)
$CLUSTER_NAME  = (terraform output -raw eks_cluster_name)
$RDS_ENDPOINT  = (terraform output -raw rds_endpoint)
$REDIS_ENDPOINT= (terraform output -raw redis_endpoint)
$AWS_REGION    = (terraform output -raw aws_region 2>$null)
if (-not $AWS_REGION) { $AWS_REGION = "us-east-1" }

Write-Host "  ECR Backend:  $ECR_BACKEND" -ForegroundColor Green
Write-Host "  ECR Frontend: $ECR_FRONTEND" -ForegroundColor Green
Write-Host "  EKS Cluster:  $CLUSTER_NAME" -ForegroundColor Green

# ── STEP 2: Authenticate Docker to ECR ───────────────────────────────────────
Write-Host "`n[2/7] Logging Docker into ECR..." -ForegroundColor Cyan
$ECR_TOKEN = (aws ecr get-login-password --region $AWS_REGION)
docker login --username AWS --password $ECR_TOKEN "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
if ($LASTEXITCODE -ne 0) { Write-Error "ECR login failed"; exit 1 }

# ── STEP 3: Build and push Docker images ─────────────────────────────────────
Write-Host "`n[3/7] Building and pushing Docker images..." -ForegroundColor Cyan
Set-Location $ROOT

docker build -f infra/docker/Dockerfile.backend -t "${ECR_BACKEND}:latest" .
if ($LASTEXITCODE -ne 0) { Write-Error "Backend Docker build failed"; exit 1 }
docker push "${ECR_BACKEND}:latest"

docker build -f infra/docker/Dockerfile.frontend -t "${ECR_FRONTEND}:latest" .
if ($LASTEXITCODE -ne 0) { Write-Error "Frontend Docker build failed"; exit 1 }
docker push "${ECR_FRONTEND}:latest"

Write-Host "  Images pushed to ECR." -ForegroundColor Green

# ── STEP 4: Configure kubectl to talk to EKS ─────────────────────────────────
Write-Host "`n[4/7] Configuring kubectl for EKS..." -ForegroundColor Cyan
aws eks update-kubeconfig --name $CLUSTER_NAME --region $AWS_REGION
if ($LASTEXITCODE -ne 0) { Write-Error "kubectl config failed"; exit 1 }

# ── STEP 5: Create K8s Secrets and ConfigMap ─────────────────────────────────
Write-Host "`n[5/7] Creating K8s secrets and ConfigMap..." -ForegroundColor Cyan

# Load .env file values
$ENV_FILE = "$ROOT\.env"
$ENV_VARS = @{}
Get-Content $ENV_FILE | Where-Object { $_ -match "^[^#]" -and $_ -match "=" } | ForEach-Object {
    $parts = $_ -split "=", 2
    $ENV_VARS[$parts[0].Trim()] = $parts[1].Trim()
}

$DB_PASSWORD = $ENV_VARS["DB_PASSWORD"]
if (-not $DB_PASSWORD) {
    $DB_PASSWORD = Read-Host "Enter the PostgreSQL password you chose" -AsSecureString
    $DB_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($DB_PASSWORD))
}

$db_user = if ($ENV_VARS["db_username"]) { $ENV_VARS["db_username"] } else { "ai_interviewer_admin" }
$DATABASE_URL = "postgresql+asyncpg://${db_user}:${DB_PASSWORD}@${RDS_ENDPOINT}:5432/ai_interviewer"
$REDIS_URL    = "redis://${REDIS_ENDPOINT}:6379/0"
$ALB_URL      = "http://$(kubectl get ingress ai-interviewer-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>$null)"

# Create ConfigMap (non-sensitive values)
kubectl create configmap ai-interviewer-config `
    --from-literal=APP_ENV=production `
    --from-literal=DEBUG=false `
    --from-literal=PYTHONPATH=/app `
    --from-literal=LLM_BASE_URL=$($ENV_VARS["LLM_BASE_URL"]) `
    --from-literal=OPENAI_MODEL=$($ENV_VARS["OPENAI_MODEL"]) `
    --from-literal=UPLOAD_DIR=/app/uploads `
    --from-literal=JWT_ALGORITHM=HS256 `
    --from-literal=JWT_EXPIRATION_MINUTES=1440 `
    --from-literal=NEXT_PUBLIC_API_URL="$ALB_URL" `
    --dry-run=client -o yaml | kubectl apply -f -

# Create Secret (sensitive values)
kubectl create secret generic ai-interviewer-secrets `
    --from-literal=SECRET_KEY=$($ENV_VARS["SECRET_KEY"]) `
    --from-literal=JWT_SECRET=$($ENV_VARS["JWT_SECRET"]) `
    --from-literal=DATABASE_URL=$DATABASE_URL `
    --from-literal=REDIS_URL=$REDIS_URL `
    --from-literal=OPENAI_API_KEY=$($ENV_VARS["OPENAI_API_KEY"]) `
    --from-literal=DEEPGRAM_API_KEY=$($ENV_VARS["DEEPGRAM_API_KEY"]) `
    --from-literal=TAVUS_API_KEY=$($ENV_VARS["TAVUS_API_KEY"]) `
    --dry-run=client -o yaml | kubectl apply -f -

# ── STEP 6: Patch image URLs and apply K8s manifests ─────────────────────────
Write-Host "`n[6/7] Deploying to Kubernetes..." -ForegroundColor Cyan

# Replace placeholder image URLs with real ECR URLs
(Get-Content "$ROOT\infra\k8s\backend.yaml")  -replace "PLACEHOLDER_ECR_BACKEND_URL",  $ECR_BACKEND  | kubectl apply -f -
(Get-Content "$ROOT\infra\k8s\frontend.yaml") -replace "PLACEHOLDER_ECR_FRONTEND_URL", $ECR_FRONTEND | kubectl apply -f -
kubectl apply -f "$ROOT\infra\k8s\database.yaml"
kubectl apply -f "$ROOT\infra\k8s\ingress.yaml"

# ── STEP 7: Wait and print access URL ────────────────────────────────────────
Write-Host "`n[7/7] Waiting for LoadBalancer to become ready (up to 3 mins)..." -ForegroundColor Cyan
$TRIES = 0
$ALB_HOST = ""
while (-not $ALB_HOST -and $TRIES -lt 12) {
    Start-Sleep -Seconds 15
    $TRIES++
    $ALB_HOST = kubectl get ingress ai-interviewer-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>$null
    Write-Host "  Attempt $TRIES/12 - ALB: $ALB_HOST"
}

Write-Host ""
if ($ALB_HOST) {
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  DEPLOYMENT COMPLETE!" -ForegroundColor Green
    Write-Host "  App URL  : http://$ALB_HOST" -ForegroundColor Yellow
    Write-Host "  API URL  : http://$ALB_HOST/api" -ForegroundColor Yellow
    Write-Host "  API Docs : http://$ALB_HOST/api/docs" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Green
} else {
    Write-Host "  ALB not ready yet -- run: kubectl get ingress" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  REMEMBER: Run 'cd infra\terraform && terraform destroy -auto-approve' to delete all AWS resources!" -ForegroundColor Red
