output "websocket_api_endpoint" {
  description = "WebSocket API endpoint URL"
  value       = aws_apigatewayv2_stage.websocket.invoke_url
}

output "websocket_api_id" {
  description = "WebSocket API ID"
  value       = aws_apigatewayv2_api.websocket.id
}

output "websocket_handler_function_name" {
  description = "WebSocket Handler Lambda function name"
  value       = aws_lambda_function.websocket_handler.function_name
}

output "processor_function_name" {
  description = "Processor Lambda function name"
  value       = aws_lambda_function.processor.function_name
}

output "websocket_url" {
  description = "WebSocket connection URL"
  value       = "${replace(aws_apigatewayv2_stage.websocket.invoke_url, "https://", "wss://")}"
}
