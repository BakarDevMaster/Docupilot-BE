import sys
import os
import traceback

# Add the backend directory to Python path for Vercel
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from mangum import Mangum
    from src.main import app
    
    # Vercel (or AWS Lambda-like) handler for FastAPI app
    handler = Mangum(app)
except Exception as e:
    # Error handler for import failures - log and return error
    error_msg = f"Import error: {str(e)}\n{traceback.format_exc()}"
    print(error_msg)
    
    def error_handler(event, context):
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": f'{{"error": "Initialization failed", "detail": "Check server logs for details"}}'
        }
    handler = error_handler

