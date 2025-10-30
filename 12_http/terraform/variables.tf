variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "websocket-lambda"
}

variable "stage_name" {
  description = "API Gateway stage name"
  type        = string
  default     = "dev"
}
