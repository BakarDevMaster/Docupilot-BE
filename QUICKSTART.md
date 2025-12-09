# 🚀 Quick Start Guide

## Step-by-Step Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Note:** If you encounter issues with `sentence-transformers` or `torch`, you can install them separately:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers
```

### 2. Create .env File

Create a `.env` file in the `backend` directory with your environment variables (see `ENV_SETUP.md` for template).

**Minimum required variables:**
```env
DATABASE_URL=your_database_url
GEMINI_API_KEY=your_gemini_key
SECRET_KEY=your_secret_key
```

### 3. Run the Server

```bash
python run.py
```

Or:
```bash
uvicorn src.main:app --reload
```

### 4. Access Swagger UI

Open your browser and go to:
**http://localhost:8000/docs** or **http://127.0.0.1:8000/docs**

**Important:** Use `localhost` or `127.0.0.1`, NOT `0.0.0.0` in your browser!

## 📖 Using Swagger UI

### Step 1: Register a User

1. In Swagger UI, find `POST /api/auth/register`
2. Click "Try it out"
3. Fill in the request body:
```json
{
  "name": "Test User",
  "email": "test@example.com",
  "password": "Test1234",
  "role": "developer"
}
```
4. Click "Execute"
5. Copy the user ID from the response (you'll need it)

### Step 2: Login

1. Find `POST /api/auth/login`
2. Click "Try it out"
3. Fill in the form:
   - **username**: `test@example.com` (your email)
   - **password**: `Test1234`
4. Click "Execute"
5. **Copy the access_token** from the response

### Step 3: Authorize in Swagger

1. Click the **"Authorize"** button at the top right of Swagger UI
2. In the "Value" field, enter: `Bearer <your_access_token>`
   - Example: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
3. Click "Authorize" then "Close"
4. Now all protected endpoints will automatically use your token

### Step 4: Test Document Endpoints

1. **Create a document:**
   - Find `POST /api/documents/`
   - Click "Try it out"
   - Fill in:
   ```json
   {
     "title": "My First Document",
     "content": "This is a test document content...",
     "doc_type": "api"
   }
   ```
   - Click "Execute"

2. **Generate a document with AI:**
   - Find `POST /api/documents/generate`
   - Click "Try it out"
   - Fill in:
   ```json
   {
     "title": "API Documentation",
     "source": "This is a REST API for user management with endpoints for create, read, update, and delete operations.",
     "doc_type": "api"
   }
   ```
   - Click "Execute"
   - Wait for the AI to generate the document (may take 10-30 seconds)

3. **List documents:**
   - Find `GET /api/documents/`
   - Click "Try it out" then "Execute"

4. **Get a specific document:**
   - Find `GET /api/documents/{doc_id}`
   - Click "Try it out"
   - Enter a document ID from the list
   - Click "Execute"

## 🎯 Common Endpoints to Test

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user (requires auth)

### Documents
- `POST /api/documents/` - Create document
- `GET /api/documents/` - List all documents
- `GET /api/documents/{doc_id}` - Get specific document
- `PUT /api/documents/{doc_id}` - Update document
- `POST /api/documents/generate` - Generate with AI
- `POST /api/documents/update` - Update with AI agent
- `GET /api/documents/{doc_id}/versions` - Get version history

### Embeddings
- `POST /api/embeddings/create` - Create embeddings
- `POST /api/embeddings/search` - Search similar content
- `GET /api/embeddings/doc/{doc_id}` - Get document embeddings

## ⚠️ Troubleshooting

### "Module not found" errors
- Make sure you're in the `backend` directory
- Activate your virtual environment
- Run: `pip install -r requirements.txt`

### Database connection errors
- Check your `DATABASE_URL` in `.env`
- Make sure the database is accessible
- For Neon: Check if the connection string is correct

### "GEMINI_API_KEY not found"
- Make sure `.env` file exists in `backend/` directory
- Check that `GEMINI_API_KEY` is set in `.env`
- Restart the server after adding environment variables

### Port 8000 already in use
- Change port in `run.py`: `port=8001`
- Or use: `uvicorn src.main:app --port 8001`

### Swagger UI not loading
- Make sure server is running
- Check console for errors
- Try: http://localhost:8000/docs (not /swagger)

## 📝 Tips

1. **Keep Swagger UI open** - It's the easiest way to test all endpoints
2. **Check the response** - Swagger shows status codes and response bodies
3. **Use the "Authorize" button** - Saves you from manually adding tokens to each request
4. **Check server logs** - The terminal shows request logs and errors
5. **Test health endpoint first** - `GET /health` to verify server is running

## 🔗 Alternative Documentation

- **ReDoc**: http://localhost:8000/redoc (alternative UI)
- **OpenAPI JSON**: http://localhost:8000/openapi.json (raw schema)

