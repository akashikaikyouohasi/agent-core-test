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

variable "agentcore_runtime_arn" {
  description = "Amazon Bedrock AgentCore Runtime ARN (e.g., arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/my_agent-xxxxx)"
  type        = string
}
