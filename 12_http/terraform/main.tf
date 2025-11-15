terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# WebSocket API Gateway
resource "aws_apigatewayv2_api" "websocket" {
  name                       = "${var.project_name}-websocket-api"
  protocol_type              = "WEBSOCKET"
  route_selection_expression = "$request.body.action"
}

# API Gateway Stage
resource "aws_apigatewayv2_stage" "websocket" {
  api_id      = aws_apigatewayv2_api.websocket.id
  name        = var.stage_name
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 5000
    throttling_rate_limit  = 10000
  }
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.project_name}"
  retention_in_days = 7
}

# Lambda Function - WebSocket Handler
data "archive_file" "websocket_handler" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/websocket_handler"
  output_path = "${path.module}/websocket_handler.zip"
}

resource "aws_lambda_function" "websocket_handler" {
  filename         = data.archive_file.websocket_handler.output_path
  function_name    = "${var.project_name}-websocket-handler"
  role            = aws_iam_role.lambda_websocket.arn
  handler         = "app.lambda_handler"
  source_code_hash = data.archive_file.websocket_handler.output_base64sha256
  runtime         = "python3.11"
  timeout         = 120  # AgentCore can take longer to respond

  environment {
    variables = {
      AGENTCORE_RUNTIME_ARN = var.agentcore_runtime_arn
    }
  }
}

# CloudWatch Log Groups for Lambda
resource "aws_cloudwatch_log_group" "websocket_handler" {
  name              = "/aws/lambda/${aws_lambda_function.websocket_handler.function_name}"
  retention_in_days = 7
}

# IAM Role for WebSocket Handler Lambda
resource "aws_iam_role" "lambda_websocket" {
  name = "${var.project_name}-lambda-websocket-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for WebSocket Handler Lambda
resource "aws_iam_role_policy" "lambda_websocket" {
  name = "${var.project_name}-lambda-websocket-policy"
  role = aws_iam_role.lambda_websocket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "execute-api:ManageConnections"
        ]
        Resource = "${aws_apigatewayv2_api.websocket.execution_arn}/*/*/@connections/*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock-agentcore:InvokeAgentRuntime"
        ]
        Resource = "${var.agentcore_runtime_arn}*"
      }
    ]
  })
}

# Lambda Permission for API Gateway to invoke WebSocket Handler
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.websocket_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket.execution_arn}/*/*"
}

# API Gateway Integrations
resource "aws_apigatewayv2_integration" "connect" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.websocket_handler.invoke_arn
}

resource "aws_apigatewayv2_integration" "disconnect" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.websocket_handler.invoke_arn
}

resource "aws_apigatewayv2_integration" "default" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.websocket_handler.invoke_arn
}

# API Gateway Routes
resource "aws_apigatewayv2_route" "connect" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$connect"
  target    = "integrations/${aws_apigatewayv2_integration.connect.id}"
}

resource "aws_apigatewayv2_route" "disconnect" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$disconnect"
  target    = "integrations/${aws_apigatewayv2_integration.disconnect.id}"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.default.id}"
}
