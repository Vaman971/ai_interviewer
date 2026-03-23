variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "db_username" {
  description = "Database administrator username"
  type        = string
  default     = "ai_interviewer_admin"
}

variable "db_password" {
  description = "Database administrator password (must be passed via secrets)"
  type        = string
  sensitive   = true
}
