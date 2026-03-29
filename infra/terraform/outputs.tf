# Outputs — printed after terraform apply, needed for the K8s deployment step

output "aws_account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "ecr_backend_url" {
  description = "ECR URL for the backend image -- use this in K8s manifests"
  value       = data.aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_url" {
  description = "ECR URL for the frontend image -- use this in K8s manifests"
  value       = data.aws_ecr_repository.frontend.repository_url
}

output "eks_cluster_name" {
  description = "EKS cluster name — use for kubectl config update"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = module.eks.cluster_endpoint
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint — use as DATABASE_URL host"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
  sensitive   = true
}
