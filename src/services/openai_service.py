"""
AI Service wrapper - uses Gemini for chat completions.
This maintains OpenAI SDK-like interface for consistency.
"""
from typing import List, Dict, Optional
import os
from src.services.gemini_service import GeminiService

class OpenAIService:
    """
    Service wrapper that uses Gemini API but maintains OpenAI SDK interface.
    This allows agents to use a consistent interface while using Gemini.
    """
    
    def __init__(self):
        # Use Gemini service internally
        self.gemini = GeminiService()
        self.model = os.getenv("GEMINI_MODEL", "gemini-pro")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a chat completion using Gemini (OpenAI SDK interface).
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated text response
        """
        return await self.gemini.chat_completion(messages, temperature, max_tokens)
    
    async def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None
    ) -> Dict:
        """
        Generate completion with function calling/tools support using Gemini.
        
        Args:
            messages: List of message dicts
            tools: Optional list of tool definitions
            tool_choice: Optional tool choice strategy
        
        Returns:
            Response dict with content and tool calls
        """
        return await self.gemini.generate_with_tools(messages, tools, tool_choice)

