variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "finsight"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "ap-south-1"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "finsight"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "finsight"
  sensitive   = true
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "backend_cpu" {
  description = "CPU units for backend ECS task (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "backend_memory" {
  description = "Memory (MB) for backend ECS task"
  type        = number
  default     = 1024
}

variable "backend_desired_count" {
  description = "Number of backend ECS tasks"
  type        = number
  default     = 2
}

variable "frontend_cpu" {
  description = "CPU units for frontend ECS task"
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "Memory (MB) for frontend ECS task"
  type        = number
  default     = 512
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "finsight.example.com"
}
