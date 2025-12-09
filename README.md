# DocuPilot Backend

AI Technical Documentation Generator - Backend API

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- PostgreSQL database (or use Neon cloud database)
- API keys for:
  - Gemini API
  - Pinecone (optional, for vector search)

### Installation

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Create virtual environment (recommended):**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
   - Create a `.env` file in the `backend` directory
   - Copy the variables from `ENV_SETUP.md` and fill in your values
   - Make sure `DATABASE_URL` points to your PostgreSQL database

### Running the Server

**Option 1: Using the run script**
```bash
python run.py
```

**Option 2: Using uvicorn directly**
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Option 3: Using Python module**
```bash
python -m uvicorn src.main:app --reload
```

The server will start on `http://127.0.0.1:8000` or `http://localhost:8000`

## 📚 API Documentation (Swagger UI)

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Using Swagger UI

1. Open http://localhost:8000/docs in your browser
2. You'll see all available endpoints organized by tags:
   - **auth**: Authentication endpoints
   - **documents**: Document CRUD and agent operations
   - **embeddings**: Vector embedding operations

3. **Testing Endpoints:**
   - Click on any endpoint to expand it
   - Click "Try it out" button
   - Fill in the required parameters
   - Click "Execute" to send the request
   - View the response below

### Authentication in Swagger

Most endpoints require authentication. To test protected endpoints:

1. First, register a user using `POST /api/auth/register`
2. Then login using `POST /api/auth/login` to get an access token
3. Click the "Authorize" button at the top of Swagger UI
4. Enter: `Bearer <your_access_token>`
5. Click "Authorize" and "Close"
6. Now all protected endpoints will use this token automatically

## 🧪 Testing the API

### 1. Health Check
```bash
GET http://localhost:8000/health
```

### 2. Register a User
```bash
POST http://localhost:8000/api/auth/register
Body:
{
  "name": "Test User",
  "email": "test@example.com",
  "password": "Test1234",
  "role": "developer"
}
```

### 3. Login
```bash
POST http://localhost:8000/api/auth/login
Form data:
- username: test@example.com
- password: Test1234
```

### 4. Create a Document
```bash
POST http://localhost:8000/api/documents/
Headers:
  Authorization: Bearer <your_token>
Body:
{
  "title": "My First Document",
  "content": "This is the content of my document...",
  "doc_type": "api"
}
```

### 5. Generate Document with AI
```bash
POST http://localhost:8000/api/documents/generate
Headers:
  Authorization: Bearer <your_token>
Body:
{
  "title": "API Documentation",
  "source": "This is a REST API for user management...",
  "doc_type": "api"
}
```

## 📁 Project Structure

```
backend/
├── src/
│   ├── api/          # API endpoints
│   ├── agents/       # AI agents (generator, maintenance)
│   ├── db/           # Database models and repositories
│   ├── services/     # External services (Gemini, Pinecone, embeddings)
│   ├── utils/        # Utilities (auth, validators, exceptions)
│   └── main.py       # FastAPI application
├── tests/            # Test files
├── requirements.txt  # Python dependencies
├── .env             # Environment variables (create this)
└── run.py           # Server startup script
```

## 🔧 Troubleshooting

### Database Connection Issues
- Verify your `DATABASE_URL` in `.env` is correct
- Make sure PostgreSQL is running (if using local database)
- Check network connectivity for cloud databases

### Import Errors
- Make sure you're in the `backend` directory
- Verify virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Port Already in Use
- Change the port in `run.py` or use: `uvicorn src.main:app --port 8001`

### Module Not Found
- Make sure you're running from the `backend` directory
- Check that `src/` directory exists and has all files

## 📝 Environment Variables

See `ENV_SETUP.md` for detailed environment variable setup.

## 🐳 Docker (Optional)

```bash
docker-compose up --build
```

## 📖 API Endpoints Summary

- **Auth**: `/api/auth/*` - Registration, login, user management
- **Documents**: `/api/documents/*` - CRUD operations, AI generation, versioning
- **Embeddings**: `/api/embeddings/*` - Vector embeddings and search

For full API documentation, visit http://localhost:8000/docs when the server is running.

