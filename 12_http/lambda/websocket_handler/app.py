import json
import os
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
lambda_client = boto3.client('lambda')
apigateway_client = boto3.client('apigatewaymanagementapi')


def lambda_handler(event, context):
    """
    WebSocket API Gateway Lambda Handler
    Handles $connect, $disconnect, and $default routes
    """
    logger.info(f"Event: {json.dumps(event)}")

    route_key = event.get('requestContext', {}).get('routeKey')
    connection_id = event.get('requestContext', {}).get('connectionId')

    if route_key == '$connect':
        return handle_connect(event, connection_id)
    elif route_key == '$disconnect':
        return handle_disconnect(event, connection_id)
    elif route_key == '$default':
        return handle_message(event, connection_id)
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Unknown route'})
        }


def handle_connect(event, connection_id):
    """Handle WebSocket connection"""
    logger.info(f"Client connected: {connection_id}")

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Connected successfully'})
    }


def handle_disconnect(event, connection_id):
    """Handle WebSocket disconnection"""
    logger.info(f"Client disconnected: {connection_id}")

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Disconnected successfully'})
    }


def handle_message(event, connection_id):
    """
    Handle incoming WebSocket messages
    Invokes the processor Lambda and sends response back to client
    """
    try:
        # Parse incoming message
        body = event.get('body', '{}')
        message_data = json.loads(body) if isinstance(body, str) else body

        logger.info(f"Received message from {connection_id}: {message_data}")

        # Get API Gateway endpoint for sending messages back
        domain_name = event['requestContext']['domainName']
        stage = event['requestContext']['stage']
        endpoint_url = f"https://{domain_name}/{stage}"

        # Initialize API Gateway Management API client with correct endpoint
        apigw_management = boto3.client(
            'apigatewaymanagementapi',
            endpoint_url=endpoint_url
        )

        # Invoke processor Lambda
        processor_function_name = os.environ.get('PROCESSOR_FUNCTION_NAME')

        processor_payload = {
            'connectionId': connection_id,
            'message': message_data
        }

        logger.info(f"Invoking processor Lambda: {processor_function_name}")

        response = lambda_client.invoke(
            FunctionName=processor_function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(processor_payload)
        )

        # Parse processor response
        processor_result = json.loads(response['Payload'].read())
        logger.info(f"Processor response: {processor_result}")

        # Extract the result from processor
        result_body = processor_result.get('body', '{}')
        if isinstance(result_body, str):
            result_data = json.loads(result_body)
        else:
            result_data = result_body

        # Send response back to WebSocket client
        response_message = {
            'action': 'response',
            'data': result_data,
            'timestamp': event['requestContext']['requestTimeEpoch']
        }

        apigw_management.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(response_message).encode('utf-8')
        )

        logger.info(f"Sent response to client {connection_id}")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Message processed successfully'})
        }

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)

        # Try to send error message back to client
        try:
            error_message = {
                'action': 'error',
                'error': str(e),
                'timestamp': event['requestContext']['requestTimeEpoch']
            }

            apigw_management.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(error_message).encode('utf-8')
            )
        except Exception as send_error:
            logger.error(f"Failed to send error to client: {str(send_error)}")

        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
