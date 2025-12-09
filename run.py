"""
Simple script to run the FastAPI server.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",  # Use localhost instead of 0.0.0.0 for browser access
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )

