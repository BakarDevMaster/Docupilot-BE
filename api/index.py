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

# Try importing step by step to identify the failing import
try:
    print("Step 1: Importing mangum...")
    from mangum import Mangum
    print("✓ Mangum imported successfully")
except Exception as e:
    init_error = f"Failed to import mangum: {str(e)}\n{traceback.format_exc()}"
    print(init_error)

if not init_error:
    try:
        print("Step 2: Importing FastAPI app...")
        from src.main import app
        print("✓ FastAPI app imported successfully")
    except Exception as e:
        init_error = f"Failed to import FastAPI app: {str(e)}\n{traceback.format_exc()}"
        print(init_error)

if not init_error:
    try:
        print("Step 3: Creating Mangum handler...")
        handler = Mangum(app)
        print("✓ Handler created successfully")
    except Exception as e:
        init_error = f"Failed to create handler: {str(e)}\n{traceback.format_exc()}"
        print(init_error)

if init_error:
    # Create error handler that returns the actual error
    def error_handler(request):
        error_msg = init_error[:2000] if len(init_error) > 2000 else init_error
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Initialization failed",
                "detail": error_msg
            })
        }
    handler = error_handler
    print("Error handler created due to initialization failure")

