# Environment Variables Setup

Create a `.env` file in the `backend` directory with the following variables:

## Database
```env
DATABASE_URL=postgresql://neondb_owner:npg_8qXKWgi4lMnC@ep-little-dust-adg6vk4x-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

## Gemini API (for chat completions)
```env
GEMINI_API_KEY=AIzaSyCDlRPQiQoPrYDmpdi_c5CraJYS1wv7n-g
GEMINI_MODEL=gemini-2.0-flash
```

## Embeddings (Free Models)
### Option 1: Local Sentence Transformers (Recommended - Free)
```env
USE_HF_API=false
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

### Option 2: Hugging Face Inference API (Free tier available)
```env
USE_HF_API=true
HUGGINGFACE_API_KEY=your_hf_api_key_here
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

## Pinecone (Vector Database)
```env
PINECONE_API_KEY=pcsk_ohJsT_KoaSH5UuSPT4HPvQrrwkoJePWBrYXNePTnNygExFYikch1MyRG6fXCJtsVCh4kc
PINECONE_INDEX_NAME=docupilot
PINECONE_REGION=us-east-1
```

## JWT Authentication
```env
SECRET_KEY=hfjtutjm6ifim4mdnfj4i59jfkt93ko958jn3snmckslo32cgh
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
```

## Cloudinary (Optional - for file uploads)
```env
CLOUDINARY_CLOUD_NAME=dv3kx5ytd
CLOUDINARY_API_KEY=757439661621122
CLOUDINARY_API_SECRET=hCpsqgtvQX3wC2-0ruWCfVqYgr8
CLOUDINARY_UPLOAD_FOLDER=docupilot
```

## Notes

- **Gemini API**: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Embeddings**: The default model `all-MiniLM-L6-v2` is free, fast, and produces 384-dimensional embeddings
- **Pinecone**: Free tier available at [Pinecone](https://www.pinecone.io/)
- **Hugging Face**: Free tier available at [Hugging Face](https://huggingface.co/)

