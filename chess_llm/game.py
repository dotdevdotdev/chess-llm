"""
Chess game logic module using python-chess library
"""
import chess
import chess.pgn
import io
from typing import Optional, Tuple, Dict, Any
import json


class ChessGame:
    def __init__(self):
        """Initialize a new chess game."""
        self.board = chess.Board()
        self.game_history = []
        self.move_times = []
        self.resigned = None  # Track which player resigned
        self.draw_accepted = False  # Track if draw was accepted
        
    def get_board_fen(self) -> str:
        """Get the current board position in FEN notation."""
        return self.board.fen()
    
    def get_board_svg(self) -> str:
        """Get SVG representation of the current board."""
        return str(self.board)
    
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.board.is_game_over() or self.resigned is not None or self.draw_accepted
    
    def get_game_result(self) -> Optional[str]:
        """Get the game result if game is over."""
        if self.resigned:
            return "resignation"
        elif self.draw_accepted:
            return "draw_accepted"
        elif self.board.is_checkmate():
            return "checkmate"
        elif self.board.is_stalemate():
            return "stalemate"
        elif self.board.is_insufficient_material():
            return "insufficient_material"
        elif self.board.is_seventyfive_moves():
            return "seventyfive_moves"
        elif self.board.is_fivefold_repetition():
            return "fivefold_repetition"
        return None
    
    def get_legal_moves(self) -> list:
        """Get list of legal moves in UCI format."""
        return [move.uci() for move in self.board.legal_moves]
    
    def make_move(self, move_uci: str, move_time: float = 0.0) -> bool:
        """
        Make a move on the board.
        
        Args:
            move_uci: Move in UCI format (e.g., "e2e4")
            move_time: Time taken to make the move in seconds
            
        Returns:
            bool: True if move was successful, False otherwise
        """
        try:
            move = chess.Move.from_uci(move_uci)
            if move in self.board.legal_moves:
                self.board.push(move)
                self.game_history.append(move_uci)
                self.move_times.append(move_time)
                return True
            return False
        except ValueError:
            return False
    
    def get_current_player(self) -> str:
        """Get the current player ('white' or 'black')."""
        return "white" if self.board.turn == chess.WHITE else "black"
    
    def get_game_state(self) -> Dict[str, Any]:
        """Get comprehensive game state."""
        return {
            "fen": self.get_board_fen(),
            "current_player": self.get_current_player(),
            "legal_moves": self.get_legal_moves(),
            "game_over": self.is_game_over(),
            "result": self.get_game_result() if self.is_game_over() else None,
            "move_history": self.game_history,
            "move_count": len(self.game_history)
        }
    
    def undo_move(self) -> bool:
        """Undo the last move."""
        if len(self.game_history) > 0:
            self.board.pop()
            self.game_history.pop()
            self.move_times.pop()
            return True
        return False
    
    def reset_game(self):
        """Reset the game to initial position."""
        self.board.reset()
        self.game_history = []
        self.move_times = []
        self.resigned = None
        self.draw_accepted = False


# Test the ChessGame class
if __name__ == "__main__":
    game = ChessGame()
    print("Initial board state:")
    print(game.get_board_fen())
    print("Legal moves:", game.get_legal_moves()[:5], "...")
    
    # Make a test move
    success = game.make_move("e2e4")
    print(f"Move e2e4 successful: {success}")
    print("New board state:", game.get_board_fen())
    print("Current player:", game.get_current_player())