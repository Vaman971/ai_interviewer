variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "db_username" {
  description = "PostgreSQL admin username"
  type        = string
  default     = "ai_interviewer_admin"
}

variable "db_password" {
  description = "PostgreSQL admin password (passed via TF_VAR_db_password env var)"
  type        = string
  sensitive   = true
}
