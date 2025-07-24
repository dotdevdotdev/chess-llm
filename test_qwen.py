#!/usr/bin/env python3
"""Test script to debug Qwen API responses"""

import os
import dashscope
from chess_llm.agents import LLMAgent, load_config

# Check if API key is available
api_key = os.getenv("ALIBABA_CLOUD_API_KEY")
if not api_key:
    print("ALIBABA_CLOUD_API_KEY not found in environment")
    exit(1)

print(f"Using API key: {api_key[:10]}...")

# Load config and create agent
config = load_config()

try:
    agent = LLMAgent(config, 'qwen', 'qwen-max')
    print("Successfully created Qwen agent")
    
    # Test with a simple chess move request
    messages = [
        {"role": "system", "content": "You are a chess player. Reply with only a chess move in UCI format."},
        {"role": "user", "content": "Current position: starting position. Legal moves: e2e4, d2d4, g1f3, b1c3. Choose a move."}
    ]
    
    print("\nSending test message to Qwen...")
    response, time_taken = agent.send_message(messages, max_tokens=10)
    
    print(f"\nResponse: '{response}'")
    print(f"Response type: {type(response)}")
    print(f"Response length: {len(response)}")
    print(f"Time taken: {time_taken:.2f}s")
    
    # Test the raw API call directly
    print("\n\nTesting raw dashscope API call...")
    dashscope.api_key = api_key
    
    raw_response = dashscope.Generation.call(
        model='qwen-max',
        messages=messages,
        temperature=0.7,
        max_tokens=10
    )
    
    print(f"Raw response type: {type(raw_response)}")
    print(f"Raw response: {raw_response}")
    
    if hasattr(raw_response, '__dict__'):
        print(f"Raw response attributes: {raw_response.__dict__}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()