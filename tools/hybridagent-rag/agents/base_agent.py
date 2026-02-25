"""
Base Agent class for all specialized agents
"""

import requests
import json
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system
    """
    
    def __init__(
        self,
        name: str,
        model: str = "gemma2",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7
    ):
        self.name = name
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.api_url = f"{base_url}/api/generate"
        self.chat_url = f"{base_url}/api/chat"
        
    def query_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 1000
    ) -> str:
        """
        Query the LLM with a prompt
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override default temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLM response text
        """
        temp = temperature if temperature is not None else self.temperature
        
        # Use chat API if system prompt provided
        if system_prompt:
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": temp,
                    "num_predict": max_tokens
                }
            }
            url = self.chat_url
        else:
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temp,
                    "num_predict": max_tokens
                }
            }
            url = self.api_url
        
        try:
            response = requests.post(url, json=data, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                if "message" in result:
                    return result["message"]["content"]
                return result.get("response", "")
            else:
                return f"Error: HTTP {response.status_code}"
                
        except Exception as e:
            return f"Exception: {str(e)}"
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input and return output
        Must be implemented by subclasses
        """
        pass
    
    def log(self, message: str, level: str = "INFO"):
        """
        Log agent activity
        """
        print(f"[{self.name}] [{level}] {message}")
