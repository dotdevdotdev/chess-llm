"""
Test script for the Chess LLM Orchestration System
"""
import sys
import os

# Add the parent directory to the path so we can import chess_llm
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chess_llm.orchestrator import GameOrchestrator


def test_orchestrator():
    """Test the game orchestrator."""
    print("Testing GameOrchestrator class...")
    
    # Create orchestrator
    orchestrator = GameOrchestrator()
    print("Orchestrator created successfully!")
    
    # Test initial game state
    game_state = orchestrator.game.get_game_state()
    print(f"Initial board: {game_state['fen']}")
    print(f"Current player: {game_state['current_player']}")
    print(f"Legal moves (first 5): {game_state['legal_moves'][:5]}")
    
    # Test making a move through the orchestrator
    # This is just testing the game logic, not the LLM agents
    turn_result = orchestrator.play_turn()
    if turn_result:
        if "error" in turn_result:
            print(f"Error in turn: {turn_result['error']}")
        else:
            print(f"Turn played successfully:")
            print(f"  Player: {turn_result['player']}")
            print(f"  Move: {turn_result['move']}")
            print(f"  Response time: {turn_result['response_time']:.2f}s")
            print(f"  Validation: {turn_result['validation']}")
    
    # Show updated game state
    game_state = orchestrator.game.get_game_state()
    print(f"\nUpdated board: {game_state['fen']}")
    print(f"Current player: {game_state['current_player']}")
    print(f"Legal moves (first 5): {game_state['legal_moves'][:5]}")
    
    print("\nOrchestrator test completed!")


if __name__ == "__main__":
    test_orchestrator()