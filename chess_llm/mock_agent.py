"""
Mock LLM agent for testing without API keys
"""
import time
import random
from typing import List, Tuple


class MockLLMAgent:
    """Mock agent that plays random legal moves for testing."""
    
    def __init__(self, provider: str = "mock", model: str = "mock-model"):
        self.provider = provider
        self.model = model
        
    def send_message(self, messages: List[dict], max_tokens: int = None) -> Tuple[str, float]:
        """
        Mock implementation that returns a random legal move.
        
        Args:
            messages: List of messages (we'll extract legal moves from the last one)
            max_tokens: Ignored in mock
            
        Returns:
            Tuple of (move, response_time)
        """
        # Simulate thinking time
        time.sleep(random.uniform(0.5, 2.0))
        
        # Extract legal moves from the last message
        last_message = messages[-1]['content']
        
        # Find legal moves in the message
        if 'Legal moves:' in last_message:
            moves_text = last_message.split('Legal moves:')[1].split('\n')[0]
            legal_moves = [move.strip() for move in moves_text.split(',') if move.strip()]
            
            if legal_moves:
                # Sometimes make special moves for variety
                if random.random() < 0.02:  # 2% chance to resign
                    return "RESIGN", 0.1
                elif random.random() < 0.05:  # 5% chance to request draw
                    return "REQUEST_DRAW", 0.1
                else:
                    # Return a random legal move
                    chosen_move = random.choice(legal_moves)
                    return chosen_move, random.uniform(0.5, 2.0)
        
        # Fallback
        return "e2e4", 1.0