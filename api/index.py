from mangum import Mangum
from src.main import app

# Vercel (or AWS Lambda-like) handler for FastAPI app
handler = Mangum(app)

