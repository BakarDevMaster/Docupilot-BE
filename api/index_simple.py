"""
Minimal test handler to verify Vercel Python works.
"""
import json

def handler(request):
    """Simple test handler."""
    try:
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "message": "Vercel Python handler works!",
                "method": request.get("httpMethod", "unknown"),
                "path": request.get("path", "unknown")
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Handler error",
                "detail": str(e)
            })
        }

