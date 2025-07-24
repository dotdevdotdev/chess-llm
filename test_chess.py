"""
Test file for chess game logic
"""
import sys
import os

# Add the parent directory to the path so we can import chess_llm
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chess_llm.game import ChessGame


def test_chess_game():
    """Test the chess game logic."""
    print("Testing ChessGame class...")
    
    # Create a new game
    game = ChessGame()
    print(f"Initial board: {game.get_board_fen()}")
    print(f"Current player: {game.get_current_player()}")
    print(f"Legal moves (first 5): {game.get_legal_moves()[:5]}")
    
    # Make a test move
    success = game.make_move("e2e4")
    print(f"\nMove e2e4 successful: {success}")
    print(f"New board: {game.get_board_fen()}")
    print(f"Current player: {game.get_current_player()}")
    print(f"Legal moves (first 5): {game.get_legal_moves()[:5]}")
    
    # Make another test move
    success = game.make_move("e7e5")
    print(f"\nMove e7e5 successful: {success}")
    print(f"New board: {game.get_board_fen()}")
    print(f"Current player: {game.get_current_player()}")
    print(f"Legal moves (first 5): {game.get_legal_moves()[:5]}")
    
    # Test game state
    game_state = game.get_game_state()
    print(f"\nGame state: {game_state}")
    
    # Test undo
    success = game.undo_move()
    print(f"\nUndo successful: {success}")
    print(f"Board after undo: {game.get_board_fen()}")
    
    print("\nAll tests completed!")


if __name__ == "__main__":
    test_chess_game()