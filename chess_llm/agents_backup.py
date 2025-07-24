"""
LLM agent communication classes for different providers
"""
import openai
import anthropic
import dashscope
import yaml
import os
from typing import Dict, Any, Optional
import time


class LLMAgent:
    def __init__(self, config: Dict[str, Any], provider: str, model: str):
        """
        Initialize an LLM agent with specific provider and model.
        
        Args:
            config: Configuration dictionary from YAML
            provider: Provider name (openai, anthropic, etc.)
            model: Model identifier
        """
        self.config = config
        self.provider = provider
        self.model = model
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate client based on provider."""
        provider_config = self.config['providers'][self.provider]
        api_key_env_var = provider_config['api_key_env_var']
        api_key = os.getenv(api_key_env_var)
        
        if not api_key:
            raise ValueError(f"API key not found for {self.provider} in environment variable {api_key_env_var}")
        
        if self.provider == 'openai':
            self.client = openai.OpenAI(api_key=api_key, base_url=provider_config.get('base_url'))
        elif self.provider == 'anthropic':
            self.client = anthropic.Anthropic(api_key=api_key)
        elif self.provider == 'qwen':
            dashscope.api_key = api_key
            self.client = dashscope
        # Add other providers as needed
    
    def get_model_name(self) -> str:
        """Get the actual model name from configuration."""
        return self.config['providers'][self.provider]['models'][self.model]['name']
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model-specific configuration."""
        return self.config['providers'][self.provider]['models'][self.model]
    
    def send_message(self, messages: list, max_tokens: Optional[int] = None) -> tuple:
        """
        Send a message to the LLM and get response.
        
        Args:
            messages: List of messages in the conversation
            max_tokens: Maximum tokens for response
            
        Returns:
            tuple: (response_text, response_time_in_seconds)
        """
        start_time = time.time()
        
        try:
            if self.provider == 'openai':
                response = self._send_openai_message(messages, max_tokens)
            elif self.provider == 'anthropic':
                response = self._send_anthropic_message(messages, max_tokens)
            elif self.provider == 'qwen':
                response = self._send_qwen_message(messages, max_tokens)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            end_time = time.time()
            response_time = end_time - start_time
            
            return response, response_time
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            raise Exception(f"Error sending message to {self.provider}: {str(e)}")
    
    def _send_openai_message(self, messages: list, max_tokens: Optional[int] = None) -> str:
        """Send message to OpenAI model."""
        model_config = self.get_model_config()
        model_name = self.get_model_name()
        
        params = {
            "model": model_name,
            "messages": messages,
            "temperature": model_config.get('temperature', 0.7),
        }
        
        if max_tokens:
            params["max_tokens"] = max_tokens
        elif 'max_tokens' in model_config:
            params["max_tokens"] = model_config['max_tokens']
        
        # Add custom settings
        custom_settings = model_config.get('custom_settings', {})
        params.update(custom_settings)
        
        response = self.client.chat.completions.create(**params)
        return response.choices[0].message.content
    
    def _send_anthropic_message(self, messages: list, max_tokens: Optional[int] = None) -> str:
        """Send message to Anthropic model."""
        model_config = self.get_model_config()
        model_name = self.get_model_name()
        
        # Convert OpenAI-style messages to Anthropic format
        system_message = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg['role'] == 'system':
                system_message = msg['content']
            else:
                anthropic_messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        params = {
            "model": model_name,
            "messages": anthropic_messages,
            "temperature": model_config.get('temperature', 0.7),
            "max_tokens": max_tokens or model_config.get('max_tokens', 1000)
        }
        
        if system_message:
            params["system"] = system_message
            
        # Add custom settings
        custom_settings = model_config.get('custom_settings', {})
        params.update(custom_settings)
        
        response = self.client.messages.create(**params)
        return response.content[0].text
    
    def _send_qwen_message(self, messages: list, max_tokens: Optional[int] = None) -> str:
        """Send message to Qwen model."""
        model_config = self.get_model_config()
        model_name = self.get_model_name()
        
        # Convert messages to Qwen format
        qwen_messages = []
        for msg in messages:
            qwen_messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        params = {
            "model": model_name,
            "messages": qwen_messages,
            "temperature": model_config.get('temperature', 0.7),
        }
        
        if max_tokens:
            params["max_tokens"] = max_tokens
        elif 'max_tokens' in model_config:
            params["max_tokens"] = model_config['max_tokens']
            
        # Add custom settings
        custom_settings = model_config.get('custom_settings', {})
        params.update(custom_settings)
        
        response = self.client.Generation.call(**params)
        return response.output.text


def load_config(config_path: str = "llm_config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)


# Example usage
if __name__ == "__main__":
    # Load configuration
    config = load_config()
    
    # Create agents
    # Uncomment the following lines when you have API keys set up
    # openai_agent = LLMAgent(config, 'openai', 'gpt-4')
    # anthropic_agent = LLMAgent(config, 'anthropic', 'claude-3-opus')
    # print("LLM agents initialized successfully!")