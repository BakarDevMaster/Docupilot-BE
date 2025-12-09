"""
Generator Agent - Creates new documentation from various inputs.
"""
from typing import Dict, List, Optional
from src.services.openai_service import OpenAIService
from src.services.vector_store import VectorStore

class GeneratorAgent:
    """
    Multi-step agent that generates technical documentation.
    Workflow:
    1. Understand intent
    2. Fetch embeddings context
    3. Generate documentation
    4. Validate consistency
    5. Save updates
    """
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.vector_store = VectorStore()
    
    async def generate_document(
        self,
        title: str,
        source: str,
        doc_type: str = "api",
        context_doc_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate a new document based on the provided source and context.
        
        Args:
            title: Document title
            source: Source material (code, specs, change logs, requirements)
            doc_type: Type of document (api, architecture, module, etc.)
            context_doc_ids: Optional list of document IDs to use as context
        
        Returns:
            Generated document content
        """
        # Step 1: Understand intent
        intent = await self._understand_intent(source, doc_type)
        
        # Step 2: Fetch embeddings context
        context = await self._fetch_context(source, context_doc_ids)
        
        # Step 3: Generate documentation
        document_content = await self._generate_content(
            title, source, intent, context, doc_type
        )
        
        # Step 4: Validate consistency
        validated_content = await self._validate_consistency(document_content)
        
        return {
            "title": title,
            "content": validated_content,
            "doc_type": doc_type,
            "metadata": {
                "intent": intent,
                "context_used": len(context) if context else 0
            }
        }
    
    async def _understand_intent(self, source: str, doc_type: str) -> Dict:
        """Analyze the source to understand what documentation is needed."""
        messages = [
            {
                "role": "system",
                "content": f"You are a technical documentation expert. Analyze the provided source material and determine what type of documentation needs to be created. The document type is: {doc_type}."
            },
            {
                "role": "user",
                "content": f"Analyze this source material and provide a brief summary of what documentation should be created:\n\n{source[:2000]}"
            }
        ]
        
        try:
            response = await self.openai_service.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=200
            )
            return {
                "type": doc_type,
                "summary": response,
                "source_length": len(source)
            }
        except Exception as e:
            return {
                "type": doc_type,
                "summary": f"Documentation for {doc_type}",
                "error": str(e)
            }
    
    async def _fetch_context(self, source: str, doc_ids: Optional[List[str]]) -> List[Dict]:
        """Retrieve relevant context from vector store."""
        context_results = []
        
        try:
            # Search for similar content in vector store
            # Use a summary or key terms from source for search
            search_query = source[:500] if len(source) > 500 else source
            
            # If specific doc_ids provided, search within those documents
            if doc_ids:
                for doc_id in doc_ids:
                    results = await self.vector_store.search_similar(
                        query=search_query,
                        top_k=3,
                        doc_id_filter=doc_id
                    )
                    context_results.extend(results)
            else:
                # Search across all documents
                results = await self.vector_store.search_similar(
                    query=search_query,
                    top_k=5
                )
                context_results.extend(results)
        except Exception as e:
            # If context retrieval fails, continue without context
            print(f"Context retrieval error: {e}")
        
        return context_results
    
    async def _generate_content(
        self,
        title: str,
        source: str,
        intent: Dict,
        context: List[Dict],
        doc_type: str
    ) -> str:
        """Generate documentation content using Gemini."""
        
        # Build context string from retrieved chunks
        context_text = ""
        if context:
            context_text = "\n\n## Relevant Context from Existing Documentation:\n"
            for i, ctx in enumerate(context[:5], 1):  # Limit to top 5 context chunks
                chunk_text = ctx.get("metadata", {}).get("chunk_text", ctx.get("chunk_text", ""))
                if chunk_text:
                    context_text += f"\n{i}. {chunk_text[:300]}...\n"
        
        # Build the prompt
        system_prompt = f"""You are an expert technical writer specializing in {doc_type} documentation. 
Your task is to create comprehensive, accurate, and well-structured technical documentation.

Guidelines:
- Write clear, concise, and professional documentation
- Use proper formatting with headers, code blocks, and lists
- Include examples where appropriate
- Ensure technical accuracy
- Follow best practices for {doc_type} documentation
- Make it easy to understand for both beginners and experts"""

        user_prompt = f"""Create technical documentation with the following details:

**Title:** {title}
**Document Type:** {doc_type}
**Intent:** {intent.get('summary', 'General documentation')}

**Source Material:**
{source}

{context_text}

Please generate comprehensive documentation that:
1. Clearly explains the subject matter
2. Is well-organized with proper sections
3. Includes relevant examples if applicable
4. Follows technical documentation best practices
5. Is suitable for the {doc_type} document type

Generate the complete documentation now:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            content = await self.openai_service.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=4000
            )
            return content
        except Exception as e:
            # Fallback if generation fails
            return f"""# {title}

## Overview
This document provides technical documentation for {title}.

## Source Material
{source[:1000]}

*Note: Full documentation generation encountered an error. Please review and complete manually.*
"""
    
    async def _validate_consistency(self, content: str) -> str:
        """Validate technical consistency of the generated content."""
        # Simple validation - check for basic structure
        if not content or len(content.strip()) < 50:
            return content
        
        # Optional: Add more sophisticated validation
        # For now, just return the content as-is
        # In the future, could add checks for:
        # - Technical term consistency
        # - Code example validity
        # - Link validity
        # - Formatting consistency
        
        return content
