"""
Maintenance Agent - Detects outdated content and updates documentation.
"""
from typing import Dict, List, Optional
from src.services.openai_service import OpenAIService
from src.services.vector_store import VectorStore

class MaintenanceAgent:
    """
    Agent that maintains and updates existing documentation.
    Workflow:
    1. Detect outdated sections
    2. Fetch relevant context
    3. Update specific paragraphs
    4. Ensure technical consistency
    5. Save updates
    """
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.vector_store = VectorStore()
    
    async def update_document(
        self,
        current_content: str,
        section: str,
        new_content: str,
        reason: Optional[str] = None,
        doc_id: Optional[str] = None
    ) -> Dict:
        """
        Update a specific section of a document.
        
        Args:
            current_content: Current full document content
            section: Section identifier or description
            new_content: New content for the section or update instructions
            reason: Optional reason for the update
            doc_id: Optional document ID for context retrieval
        
        Returns:
            Updated document content
        """
        # Step 1: Fetch relevant context if doc_id provided
        context = []
        if doc_id:
            context = await self._fetch_relevant_context(doc_id, section)
        
        # Step 2: Update specific section
        updated_content = await self._update_section(
            current_content, section, new_content, context, reason
        )
        
        # Step 3: Ensure technical consistency
        validated_content = await self._ensure_consistency(
            current_content, updated_content
        )
        
        return {
            "updated_content": validated_content,
            "section": section,
            "reason": reason or "Maintenance update",
            "context_used": len(context)
        }
    
    async def audit_document(self, content: str, doc_id: Optional[str] = None) -> Dict:
        """
        Audit a document for outdated content and inconsistencies.
        
        Args:
            content: Document content to audit
            doc_id: Optional document ID for context comparison
        
        Returns:
            Audit results with detected issues
        """
        outdated_sections = await self._detect_outdated_sections(content)
        inconsistencies = await self._check_consistency(content, doc_id)
        
        return {
            "outdated_sections": outdated_sections,
            "inconsistencies": inconsistencies,
            "status": "audited",
            "issues_count": len(outdated_sections) + len(inconsistencies)
        }
    
    async def _detect_outdated_sections(self, content: str) -> List[Dict]:
        """Detect which sections of a document are outdated."""
        messages = [
            {
                "role": "system",
                "content": "You are a technical documentation auditor. Analyze the provided documentation and identify sections that may be outdated, contain deprecated information, or need updates."
            },
            {
                "role": "user",
                "content": f"Analyze this documentation and identify outdated sections:\n\n{content[:3000]}"
            }
        ]
        
        try:
            response = await self.openai_service.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response to extract sections (simplified - can be enhanced)
            # For now, return a structured response
            return [{
                "section": "Detected by AI",
                "reason": response,
                "severity": "medium"
            }]
        except Exception as e:
            return []
    
    async def _fetch_relevant_context(
        self, doc_id: str, section: str
    ) -> List[Dict]:
        """Fetch relevant context for updating a section."""
        try:
            # Search for similar content in the document
            results = await self.vector_store.search_similar(
                query=section,
                top_k=3,
                doc_id_filter=doc_id
            )
            return results
        except Exception:
            return []
    
    async def _update_section(
        self,
        current_content: str,
        section: str,
        new_content: str,
        context: List[Dict],
        reason: Optional[str] = None
    ) -> str:
        """Update a specific section with new content."""
        
        # Build context string
        context_text = ""
        if context:
            context_text = "\n\n## Relevant Context:\n"
            for i, ctx in enumerate(context[:3], 1):
                chunk_text = ctx.get("metadata", {}).get("chunk_text", ctx.get("chunk_text", ""))
                if chunk_text:
                    context_text += f"\n{i}. {chunk_text[:200]}...\n"
        
        system_prompt = """You are an expert technical writer maintaining documentation. 
Your task is to update documentation sections while maintaining consistency, clarity, and technical accuracy.

Guidelines:
- Preserve the overall structure and style
- Ensure the updated section fits seamlessly with the rest of the document
- Maintain technical accuracy
- Keep formatting consistent
- Update only the specified section unless necessary for coherence"""

        user_prompt = f"""Update the following documentation section:

**Section to Update:** {section}
**Reason for Update:** {reason or "Maintenance update"}
**New Content/Instructions:** {new_content}

**Current Document Content:**
{current_content[:4000]}

{context_text}

Please provide the complete updated document content, ensuring:
1. The specified section is updated appropriately
2. The rest of the document remains unchanged unless necessary
3. Technical consistency is maintained
4. Formatting and style are preserved

Provide the complete updated document:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            updated_content = await self.openai_service.chat_completion(
                messages=messages,
                temperature=0.5,
                max_tokens=4000
            )
            return updated_content
        except Exception as e:
            # Fallback: simple text replacement if AI fails
            # This is a basic fallback - in production, you'd want better handling
            return current_content.replace(section, new_content) if section in current_content else current_content
    
    async def _ensure_consistency(
        self, original_content: str, updated_content: str
    ) -> str:
        """Ensure technical consistency across the document."""
        # Check if content changed significantly
        if not updated_content or len(updated_content.strip()) < 50:
            return original_content
        
        # Basic validation - check for common issues
        # In production, you could add more sophisticated checks:
        # - Technical term consistency
        # - Code example validity
        # - Link validity
        # - Cross-reference validity
        
        # For now, return the updated content
        # Could add a consistency check prompt here if needed
        return updated_content
    
    async def _check_consistency(self, content: str, doc_id: Optional[str] = None) -> List[Dict]:
        """Check for inconsistencies in the document."""
        messages = [
            {
                "role": "system",
                "content": "You are a technical documentation quality checker. Analyze documentation for inconsistencies, contradictions, or errors."
            },
            {
                "role": "user",
                "content": f"Check this documentation for inconsistencies:\n\n{content[:3000]}"
            }
        ]
        
        try:
            response = await self.openai_service.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=500
            )
            
            return [{
                "type": "consistency_check",
                "description": response,
                "severity": "low"
            }]
        except Exception:
            return []
