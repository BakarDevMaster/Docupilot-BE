"""
Simple test handler to verify Vercel Python setup works.
"""
def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"message": "Test handler works!", "event": "received"}'
    }

