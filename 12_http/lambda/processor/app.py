import json
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Processor Lambda Function
    Called by the WebSocket handler to process messages
    """
    logger.info(f"Processor received event: {json.dumps(event)}")

    try:
        connection_id = event.get('connectionId')
        message = event.get('message', {})

        # Extract action and data from message
        action = message.get('action', 'unknown')
        data = message.get('data', {})

        logger.info(f"Processing action '{action}' for connection {connection_id}")

        # Process based on action
        if action == 'echo':
            result = process_echo(data)
        elif action == 'uppercase':
            result = process_uppercase(data)
        elif action == 'reverse':
            result = process_reverse(data)
        elif action == 'timestamp':
            result = process_timestamp(data)
        else:
            result = {
                'action': action,
                'status': 'unknown_action',
                'message': f"Unknown action: {action}. Available actions: echo, uppercase, reverse, timestamp",
                'receivedData': data
            }

        # Add processing metadata
        result['processedAt'] = datetime.utcnow().isoformat()
        result['connectionId'] = connection_id

        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }

    except Exception as e:
        logger.error(f"Error in processor: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to process message'
            })
        }


def process_echo(data):
    """Echo back the received data"""
    return {
        'action': 'echo',
        'status': 'success',
        'message': 'Message echoed',
        'result': data
    }


def process_uppercase(data):
    """Convert text to uppercase"""
    text = data.get('text', '')
    return {
        'action': 'uppercase',
        'status': 'success',
        'message': 'Text converted to uppercase',
        'result': text.upper()
    }


def process_reverse(data):
    """Reverse the text"""
    text = data.get('text', '')
    return {
        'action': 'reverse',
        'status': 'success',
        'message': 'Text reversed',
        'result': text[::-1]
    }


def process_timestamp(data):
    """Return current timestamp"""
    return {
        'action': 'timestamp',
        'status': 'success',
        'message': 'Current timestamp',
        'result': {
            'iso': datetime.utcnow().isoformat(),
            'unix': int(datetime.utcnow().timestamp())
        }
    }
