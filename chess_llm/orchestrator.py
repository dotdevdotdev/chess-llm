"""
Orchestrator/controller for managing the chess game flow between LLM agents
"""
import random
import time
from typing import Dict, Any, Optional, Tuple
from chess_llm.game import ChessGame
from chess_llm.agents import LLMAgent, load_config


class GameOrchestrator:
    def __init__(self, config_path: str = "llm_config.yaml"):
        """
        Initialize the game orchestrator.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config = load_config(config_path)
        self.game = ChessGame()
        self.white_agent = None
        self.black_agent = None
        self.referee_agent = None
        self.move_times = {"white": [], "black": []}
        self.game_log = []
        
    def setup_agents(self, white_provider: str, white_model: str, 
                    black_provider: str, black_model: str):
        """
        Set up the LLM agents for white and black pieces.
        
        Args:
            white_provider: Provider for white agent
            white_model: Model for white agent
            black_provider: Provider for black agent
            black_model: Model for black agent
        """
        self.white_agent = LLMAgent(self.config, white_provider, white_model)
        self.black_agent = LLMAgent(self.config, black_provider, black_model)
        
        # Set up referee agent
        referee_config = self.config['referee']
        self.referee_agent = LLMAgent(
            self.config, 
            referee_config['provider'], 
            referee_config['model']
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for chess playing agents."""
        return """
You are a chess grandmaster playing a game of chess. You will receive the current board position in FEN notation and a list of legal moves. Your task is to choose the best move from the legal moves provided.

Respond with ONLY the move in UCI format (e.g., "e2e4", "g1f3") and nothing else.
Examples of valid responses: "e2e4", "g1f3", "e7e8q"

Board position is given in FEN notation.
Legal moves are provided as a list of UCI formatted moves.
"""
    
    def _get_referee_system_prompt(self) -> str:
        """Get the system prompt for the referee agent."""
        return """
You are a chess referee and validator. Your job is to:
1. Verify that chess moves are valid according to the rules
2. Validate that the board position is legal
3. Check that players are making moves on their turn
4. Detect game-ending conditions (checkmate, stalemate, etc.)

You will receive:
- Current board position in FEN notation
- The move that was played
- List of legal moves for the current position

Respond with either "VALID" if the move is correct, or "INVALID: [reason]" if there is an issue.
"""
    
    def _get_move_prompt(self, game_state: Dict[str, Any]) -> str:
        """Generate prompt for requesting a move from an agent."""
        prompt = f"""
Current board position (FEN): {game_state['fen']}
Current player: {game_state['current_player']}
Legal moves: {', '.join(game_state['legal_moves'])}

Choose the best move from the legal moves provided. Respond with ONLY the move in UCI format (e.g., "e2e4") and nothing else.
"""
        return prompt
    
    def _validate_move_with_referee(self, move: str, game_state: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate a move using the referee agent.
        
        Args:
            move: Move in UCI format
            game_state: Current game state
            
        Returns:
            Tuple of (is_valid, message)
        """
        # First check if move is in legal moves (fast local check)
        if move not in game_state['legal_moves']:
            return False, f"Move {move} is not in the list of legal moves"
        
        # For additional validation, we can use the referee agent
        try:
            referee_prompt = f"""
Validate this chess move:
- Board position (FEN): {game_state['fen']}
- Move played: {move}
- Legal moves: {', '.join(game_state['legal_moves'])}
- Current player: {game_state['current_player']}

Is this move valid? Respond with either "VALID" or "INVALID: [reason]".
"""
            
            messages = [
                {"role": "system", "content": self._get_referee_system_prompt()},
                {"role": "user", "content": referee_prompt}
            ]
            
            response, _ = self.referee_agent.send_message(messages, max_tokens=100)
            
            response_text = response.strip().upper()
            if response_text.startswith("VALID"):
                return True, "Move validated successfully"
            elif response_text.startswith("INVALID"):
                return False, response_text
            else:
                # If referee gives unexpected response, fall back to local validation
                return True, "Move validated locally (referee response unclear)"
                
        except Exception as e:
            # If referee fails, fall back to local validation
            return True, f"Local validation only (referee error: {str(e)})"
    
    def play_turn(self) -> Optional[Dict[str, Any]]:
        """
        Play one turn of the game.
        
        Returns:
            Dict with turn results or None if game is over
        """
        if self.game.is_game_over():
            return None
        
        # Determine current player
        current_player = self.game.get_current_player()
        current_agent = self.white_agent if current_player == "white" else self.black_agent
        
        # Get game state
        game_state = self.game.get_game_state()
        
        # Prepare messages for the agent
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": self._get_move_prompt(game_state)}
        ]
        
        try:
            # Get move from agent
            move_response, response_time = current_agent.send_message(messages)
            
            # Extract move (first 4 characters should be the UCI move)
            move = move_response.strip().split()[0][:4] if move_response.strip() else ""
            
            # Validate move
            is_valid, validation_message = self._validate_move_with_referee(move, game_state)
            
            if is_valid:
                # Make move
                success = self.game.make_move(move, response_time)
                if success:
                    self.move_times[current_player].append(response_time)
                    
                    # Log the turn
                    turn_log = {
                        "player": current_player,
                        "move": move,
                        "response_time": response_time,
                        "board_fen": self.game.get_board_fen(),
                        "validation": validation_message
                    }
                    self.game_log.append(turn_log)
                    
                    return turn_log
                else:
                    # Invalid move according to game logic
                    return {
                        "error": "Invalid move according to game logic",
                        "player": current_player,
                        "move": move
                    }
            else:
                # Invalid move according to referee
                return {
                    "error": f"Invalid move according to referee: {validation_message}",
                    "player": current_player,
                    "move": move,
                    "legal_moves": game_state['legal_moves']
                }
                
        except Exception as e:
            return {
                "error": f"Exception during {current_player} turn: {str(e)}",
                "player": current_player
            }
    
    def play_game(self, max_turns: int = 100) -> Dict[str, Any]:
        """
        Play a complete game.
        
        Args:
            max_turns: Maximum number of turns to play
            
        Returns:
            Dict with game results
        """
        for turn in range(max_turns):
            turn_result = self.play_turn()
            
            if turn_result is None:
                # Game is over
                break
            
            if "error" in turn_result:
                # Handle error in move
                print(f"Error in move: {turn_result}")
                # Could implement retry logic or game termination here
            
            # Check if game is over after the move
            if self.game.is_game_over():
                break
        
        # Return game results
        return {
            "game_state": self.game.get_game_state(),
            "move_times": self.move_times,
            "game_log": self.game_log,
            "winner": self._get_winner()
        }
    
    def _get_winner(self) -> Optional[str]:
        """Determine the winner of the game."""
        if not self.game.is_game_over():
            return None
        
        result = self.game.get_game_result()
        if result == "checkmate":
            # Winner is the player who just moved (opposite of current player)
            current_player = self.game.get_current_player()
            return "black" if current_player == "white" else "white"
        elif result in ["stalemate", "insufficient_material", "seventyfive_moves", "fivefold_repetition"]:
            return "draw"
        else:
            return None


# Example usage
if __name__ == "__main__":
    orchestrator = GameOrchestrator()
    
    # Set up agents (you'll need to have API keys set up in environment variables)
    # orchestrator.setup_agents("openai", "gpt-4", "anthropic", "claude-3-opus")
    
    # For testing without API keys, we can test the game logic separately
    print("Game orchestrator initialized!")
    print("Current board:", orchestrator.game.get_board_fen())