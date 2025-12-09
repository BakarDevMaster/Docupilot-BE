"""
Gemini service for chat completions using Google's Gemini API.
Uses OpenAI Agent SDK pattern for consistency.
"""
from typing import List, Dict, Optional
import os
import google.generativeai as genai

class GeminiService:
    """
    Service for interacting with Google Gemini API.
    Handles chat completions for agents using OpenAI SDK-like interface.
    """
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-pro")
        self.model = genai.GenerativeModel(self.model_name)
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a chat completion using Gemini.
        Converts OpenAI-style messages to Gemini format.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated text response
        """
        # Convert OpenAI format to Gemini format
        prompt = self._convert_messages_to_prompt(messages)
        
        generation_config = {
            "temperature": temperature,
        }
        
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens
        
        response = self.model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        return response.text
    
    async def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None
    ) -> Dict:
        """
        Generate completion with function calling/tools support.
        Note: Gemini has function calling support via tools parameter.
        
        Args:
            messages: List of message dicts
            tools: Optional list of tool definitions
            tool_choice: Optional tool choice strategy
        
        Returns:
            Response dict with content and tool calls
        """
        prompt = self._convert_messages_to_prompt(messages)
        
        # Configure tools if provided
        if tools:
            # Convert tools to Gemini format
            gemini_tools = self._convert_tools_to_gemini(tools)
            response = self.model.generate_content(
                prompt,
                tools=gemini_tools
            )
        else:
            response = self.model.generate_content(prompt)
        
        # Extract tool calls if present
        tool_calls = []
        if hasattr(response, 'function_calls') and response.function_calls:
            tool_calls = response.function_calls
        
        return {
            "content": response.text,
            "tool_calls": tool_calls
        }
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert OpenAI-style messages to a single prompt string for Gemini.
        """
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}\n")
            elif role == "user":
                prompt_parts.append(f"User: {content}\n")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}\n")
        
        return "\n".join(prompt_parts)
    
    def _convert_tools_to_gemini(self, tools: List[Dict]) -> List:
        """
        Convert OpenAI-style tools to Gemini format.
        """
        # TODO: Implement tool conversion if needed
        # Gemini uses a different tool format
        return []

