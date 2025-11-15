import json
import os
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock_agentcore_client = boto3.client('bedrock-agentcore')
apigateway_client = boto3.client('apigatewaymanagementapi')


def lambda_handler(event, context):
    """
    WebSocket API Gateway Lambda Handler
    Handles $connect, $disconnect, and $default routes
    Integrates with Amazon Bedrock AgentCore Runtime
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
    logger.info("Client connected: %s", connection_id)

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Connected successfully'})
    }


def handle_disconnect(event, connection_id):
    """Handle WebSocket disconnection"""
    logger.info("Client disconnected: %s", connection_id)

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Disconnected successfully'})
    }


def handle_message(event, connection_id):
    """
    Handle incoming WebSocket messages
    Invokes Amazon Bedrock AgentCore Runtime and sends response back to client
    """
    try:
        # Parse incoming message
        body = event.get('body', '{}')
        message_data = json.loads(body) if isinstance(body, str) else body

        logger.info("Received message from %s: %s", connection_id, message_data)

        # Get API Gateway endpoint for sending messages back
        domain_name = event['requestContext']['domainName']
        stage = event['requestContext']['stage']
        endpoint_url = f"https://{domain_name}/{stage}"

        # Initialize API Gateway Management API client with correct endpoint
        apigw_management = boto3.client(
            'apigatewaymanagementapi',
            endpoint_url=endpoint_url
        )

        # Get AgentCore Runtime ARN from environment
        agent_runtime_arn = os.environ.get('AGENTCORE_RUNTIME_ARN')
        
        if not agent_runtime_arn:
            raise ValueError("AGENTCORE_RUNTIME_ARN environment variable not set")

        # Extract session ID from message or use connection ID
        # AgentCore requires session ID to be at least 33 characters
        session_id = message_data.get('sessionId', connection_id)
        
        # Ensure session ID is at least 33 characters
        if len(session_id) < 33:
            # Pad with connection_id to ensure minimum length
            session_id = f"{session_id}-{connection_id}"[:64]  # Max 64 chars
        
        # Ensure it's exactly between 33-64 characters
        if len(session_id) < 33:
            session_id = session_id.ljust(33, '0')
        elif len(session_id) > 64:
            session_id = session_id[:64]

        # Prepare payload for AgentCore Runtime
        agentcore_payload = {
            'prompt': message_data.get('prompt', message_data.get('data', {}).get('message', '')),
            'sessionId': session_id
        }

        # Add any additional parameters from the message
        if 'parameters' in message_data:
            agentcore_payload.update(message_data['parameters'])

        logger.info("Invoking AgentCore Runtime: %s", agent_runtime_arn)
        logger.info("Payload: %s", agentcore_payload)

        # Invoke AgentCore Runtime using direct HTTP request
        import urllib.parse
        from botocore.auth import SigV4Auth
        from botocore.awsrequest import AWSRequest
        import urllib3
        
        # Extract region from ARN
        arn_parts = agent_runtime_arn.split(':')
        region = arn_parts[3] if len(arn_parts) > 3 else 'us-east-1'
        
        # Construct the endpoint URL
        encoded_arn = urllib.parse.quote(agent_runtime_arn, safe='')
        endpoint_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations"
        
        # Prepare the request payload
        request_payload = {
            'prompt': agentcore_payload.get('prompt', ''),
            'sessionId': session_id
        }
        
        payload_bytes = json.dumps(request_payload).encode('utf-8')
        
        # Get AWS credentials for signing the request
        credentials = boto3.Session().get_credentials()
        
        # Create the request
        headers = {
            'Content-Type': 'application/json',
            'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': session_id
        }
        
        aws_request = AWSRequest(
            method='POST',
            url=endpoint_url,
            data=payload_bytes,
            headers=headers
        )
        
        # Sign the request
        SigV4Auth(credentials, 'bedrock-agentcore', region).add_auth(aws_request)
        
        # Make the request using urllib3
        http = urllib3.PoolManager()
        response = http.request(
            'POST',
            endpoint_url,
            body=payload_bytes,
            headers=dict(aws_request.headers),
            timeout=115.0
        )
        
        if response.status != 200:
            raise Exception(f"AgentCore Runtime returned status {response.status}: {response.data.decode('utf-8')}")
        
        result_data = json.loads(response.data.decode('utf-8'))
        
        logger.info("AgentCore response: %s", result_data)

        # Send response back to WebSocket client
        response_message = {
            'action': 'response',
            'data': {
                'result': result_data,
                'sessionId': session_id
            },
            'timestamp': event['requestContext']['requestTimeEpoch']
        }

        apigw_management.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(response_message).encode('utf-8')
        )

        logger.info("Sent response to client %s", connection_id)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Message processed successfully'})
        }

    except Exception as e:
        logger.error("Error processing message: %s", str(e), exc_info=True)

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
            logger.error("Failed to send error to client: %s", str(send_error))

        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
