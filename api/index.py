import sys
import os
import traceback
import json

# Add the backend directory to Python path for Vercel
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Initialize handler variable
handler = None
init_error = None

try:
    from mangum import Mangum
    from src.main import app
    
    # Vercel (or AWS Lambda-like) handler for FastAPI app
    handler = Mangum(app)
    print("Handler initialized successfully")
except Exception as e:
    # Capture the error for debugging
    init_error = f"Import/Init error: {str(e)}\n{traceback.format_exc()}"
    print(init_error)
    
    # Create a simple error handler that returns the actual error
    def error_handler(event, context):
        error_detail = init_error if init_error else "Unknown initialization error"
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Initialization failed",
                "detail": error_detail[:500]  # Limit length
            })
        }
    handler = error_handler

