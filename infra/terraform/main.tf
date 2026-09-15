terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"   # EKS module v19 is incompatible with AWS provider v6
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.10.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = ">= 3.0.0"
    }
  }
  required_version = ">= 1.3.0"
}

provider "aws" {
  region = var.aws_region
}

# ── Data: Get the current AWS Account ID ─────────────────────────────
data "aws_caller_identity" "current" {}

# ── 1. VPC Configuration ─────────────────────────────────────────────
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "ai-interviewer-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = true  # One NAT GW saves ~$32/mo vs two
  enable_dns_hostnames = true
  enable_dns_support   = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }
}

# ── 2. EKS Cluster ───────────────────────────────────────────────────
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "19.16.0"

  cluster_name    = "ai-interviewer-eks"
  cluster_version = "1.31"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access = true

  eks_managed_node_groups = {
    general = {
      desired_size   = 2
      min_size       = 1
      max_size       = 3
      instance_types = ["t3.medium"]

      iam_role_additional_policies = {
        AmazonEC2ContainerRegistryReadOnly = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
      }
    }
  }
}

# ── 3. ECR Repositories (already created by CI pipeline — read-only) ─
data "aws_ecr_repository" "backend" {
  name = "ai-interviewer-backend"
}

data "aws_ecr_repository" "frontend" {
  name = "ai-interviewer-frontend"
}

# ── 4. Security Groups ───────────────────────────────────────────────

# Security group for RDS (only allow access from inside VPC)
resource "aws_security_group" "rds" {
  name        = "ai-interviewer-rds-sg"
  description = "Allow PostgreSQL from within the VPC"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Security group for Redis (only allow access from within VPC)
resource "aws_security_group" "redis" {
  name        = "ai-interviewer-redis-sg"
  description = "Allow Redis from within the VPC"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ── 5. RDS Subnet Group ──────────────────────────────────────────────
resource "aws_db_subnet_group" "rds" {
  name       = "ai-interviewer-rds-subnet-group"
  subnet_ids = module.vpc.private_subnets
}

# ── 6. RDS PostgreSQL Database ───────────────────────────────────────
resource "aws_db_instance" "postgres" {
  identifier          = "ai-interviewer-db"
  allocated_storage   = 20
  engine              = "postgres"
  engine_version      = "15"
  instance_class      = "db.t3.micro"
  db_name             = "ai_interviewer"
  username            = var.db_username
  password            = var.db_password
  skip_final_snapshot = true

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.rds.name
  publicly_accessible    = false
}

# ── 7. ElastiCache Subnet Group ──────────────────────────────────────
resource "aws_elasticache_subnet_group" "redis" {
  name       = "ai-interviewer-redis-subnet-group"
  subnet_ids = module.vpc.private_subnets
}

# ── 8. ElastiCache Redis ─────────────────────────────────────────────
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "ai-interviewer-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.1"
  port                 = 6379
  security_group_ids   = [aws_security_group.redis.id]
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
}
