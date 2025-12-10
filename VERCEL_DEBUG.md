# Vercel Deployment Debugging Guide

## Current Status
The backend is deployed on Vercel but the serverless function is crashing with a 500 error.

## How to Check Logs

1. **Vercel Dashboard → Your Project → Functions Tab**
   - Click on the function name
   - View real-time logs

2. **Vercel Dashboard → Deployments → Click Failed Deployment**
   - Scroll to "Function Logs" section
   - Look for Python traceback errors

3. **Via Vercel CLI** (if installed):
   ```bash
   vercel logs [deployment-url]
   ```

## Common Issues

### 1. Missing Environment Variables
Ensure all required env vars are set in Vercel Dashboard:
- `DATABASE_URL`
- `GEMINI_API_KEY`
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME`
- `PINECONE_USE_MANAGED=true`
- `PINECONE_MANAGED_MODEL=llama-text-embed-v2`
- `SECRET_KEY`
- `ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=43200`

### 2. Import Errors
The handler now logs step-by-step import progress. Check logs for:
- "Step 1: Importing mangum..."
- "Step 2: Importing FastAPI app..."
- "Step 3: Creating Mangum handler..."

### 3. Database Connection
Database engine is now lazy-loaded, but if `DATABASE_URL` is invalid, it may still cause issues.

### 4. Heavy Dependencies
We removed `torch` and `sentence-transformers` since you're using Pinecone-managed embeddings.

## Testing

After deployment, test these endpoints:
- `GET /health` - Should return `{"status": "healthy"}`
- `GET /` - Should return API message

If these fail, check the function logs for the actual error.

