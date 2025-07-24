"""
Async orchestrator for managing chess games between LLM agents in the web server
"""
import asyncio
import time
from typing import Dict, Any, Optional, Tuple, Callable
from chess_llm.game import ChessGame
from chess_llm.agents import LLMAgent, load_config
from chess_llm.mock_agent import MockLLMAgent


class AsyncGameOrchestrator:
    def __init__(self, config_path: str = "llm_config.yaml", game_id: str = "default"):
        """
        Initialize the async game orchestrator.
        
        Args:
            config_path: Path to the YAML configuration file
            game_id: Unique identifier for this game
        """
        self.config = load_config(config_path)
        self.game = ChessGame()
        self.game_id = game_id
        self.white_agent = None
        self.black_agent = None
        self.referee_agent = None
        self.move_times = {"white": [], "black": [], "orchestrator": 0}
        self.game_log = []
        self.is_running = False
        self.is_paused = False
        self.move_callback = None
        self.log_callback = None
        self.state_callback = None
        
    def set_callbacks(self, move_callback: Optional[Callable] = None, 
                     log_callback: Optional[Callable] = None,
                     state_callback: Optional[Callable] = None):
        """Set callback functions for game events."""
        self.move_callback = move_callback
        self.log_callback = log_callback
        self.state_callback = state_callback
        
    async def setup_agents(self, white_provider: str, white_model: str, 
                         black_provider: str, black_model: str):
        """
        Set up the LLM agents for white and black pieces.
        
        Args:
            white_provider: Provider for white agent
            white_model: Model for white agent
            black_provider: Provider for black agent
            black_model: Model for black agent
        """
        try:
            # Use mock agents if requested or if API key setup fails
            if white_provider == "mock" or white_model == "mock":
                self.white_agent = MockLLMAgent(white_provider, white_model)
                if self.log_callback:
                    await self.log_callback("Using mock agent for White player")
            else:
                try:
                    self.white_agent = LLMAgent(self.config, white_provider, white_model)
                except Exception as e:
                    if self.log_callback:
                        await self.log_callback(f"Failed to init White agent: {str(e)}, using mock", level="warning")
                    self.white_agent = MockLLMAgent("mock", "mock-white")
                    
            if black_provider == "mock" or black_model == "mock":
                self.black_agent = MockLLMAgent(black_provider, black_model)
                if self.log_callback:
                    await self.log_callback("Using mock agent for Black player")
            else:
                try:
                    self.black_agent = LLMAgent(self.config, black_provider, black_model)
                except Exception as e:
                    if self.log_callback:
                        await self.log_callback(f"Failed to init Black agent: {str(e)}, using mock", level="warning")
                    self.black_agent = MockLLMAgent("mock", "mock-black")
            
            # Always use mock referee for now to avoid API key issues
            self.referee_agent = MockLLMAgent("mock", "mock-referee")
            
            if self.log_callback:
                white_desc = f"{self.white_agent.provider}/{self.white_agent.model}"
                black_desc = f"{self.black_agent.provider}/{self.black_agent.model}"
                await self.log_callback(f"Agents initialized - White: {white_desc}, Black: {black_desc}")
                
        except Exception as e:
            if self.log_callback:
                await self.log_callback(f"Error initializing agents: {str(e)}", level="error")
            raise
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for chess playing agents."""
        return """You are a chess grandmaster playing a game of chess. You will receive the current board position in FEN notation and a list of legal moves. Your task is to choose the best move from the legal moves provided.

Respond with ONLY one of the following:
1. A move in UCI format (e.g., "e2e4", "g1f3", "e7e8q")
2. "REQUEST_DRAW" if you want to offer a draw
3. "RESIGN" if you want to resign
4. "DRAW_ACCEPTED" if the opponent offered a draw and you accept
5. "DRAW_REFUSED" if the opponent offered a draw and you refuse

Examples of valid responses: "e2e4", "g1f3", "REQUEST_DRAW", "RESIGN"

Board position is given in FEN notation.
Legal moves are provided as a list of UCI formatted moves."""
    
    def _get_move_prompt(self, game_state: Dict[str, Any], last_opponent_move: Optional[str] = None, 
                        draw_requested: bool = False) -> str:
        """Generate prompt for requesting a move from an agent."""
        prompt = f"""Current board position (FEN): {game_state['fen']}
You are playing as: {game_state['current_player'].upper()}
Legal moves: {', '.join(game_state['legal_moves'])}"""
        
        if last_opponent_move:
            prompt += f"\nOpponent's last move: {last_opponent_move}"
            
        if draw_requested:
            prompt += "\n\nYour opponent has offered a draw. You can respond with 'DRAW_ACCEPTED' or 'DRAW_REFUSED', or make a regular move to refuse."
            
        prompt += "\n\nRespond with your move in UCI format or one of the special commands (REQUEST_DRAW, RESIGN, DRAW_ACCEPTED, DRAW_REFUSED)."
        
        return prompt
    
    async def _send_invalid_move_prompt(self, agent: LLMAgent, invalid_response: str, 
                                      game_state: Dict[str, Any], last_opponent_move: Optional[str] = None) -> str:
        """Send a prompt to agent when they made an invalid move."""
        prompt = f"""Your previous response was invalid: "{invalid_response}"

Current board position (FEN): {game_state['fen']}
You are playing as: {game_state['current_player'].upper()}
Legal moves: {', '.join(game_state['legal_moves'])}"""
        
        if last_opponent_move:
            prompt += f"\nOpponent's last move: {last_opponent_move}"
            
        prompt += "\n\nPlease provide a valid move in UCI format or one of: REQUEST_DRAW, RESIGN"
        
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        response, response_time = await asyncio.to_thread(agent.send_message, messages)
        return response.strip()
    
    async def play_turn(self) -> Optional[Dict[str, Any]]:
        """
        Play one turn of the game.
        
        Returns:
            Dict with turn results or None if game is over
        """
        if self.game.is_game_over() or not self.is_running:
            return None
            
        while self.is_paused:
            await asyncio.sleep(0.1)
            if not self.is_running:
                return None
        
        # Start orchestrator timing
        orchestrator_start = time.time()
        
        # Determine current player
        current_player = self.game.get_current_player()
        current_agent = self.white_agent if current_player == "white" else self.black_agent
        
        # Get game state
        game_state = self.game.get_game_state()
        
        # Get last move for context
        last_move = None
        if self.game.game_history:
            last_move = self.game.game_history[-1]  # game_history stores moves as strings
        
        # Check if there's a pending draw offer
        draw_requested = hasattr(self.game, 'draw_requested') and self.game.draw_requested
        
        # Prepare messages for the agent
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": self._get_move_prompt(game_state, last_move, draw_requested)}
        ]
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.log_callback:
                    await self.log_callback(f"{current_player.capitalize()} is thinking...")
                
                # Get move from agent (using thread pool for sync function)
                response, response_time = await asyncio.to_thread(current_agent.send_message, messages)
                
                # Parse response
                response_text = response.strip().upper()
                
                # Update orchestrator time
                orchestrator_time = time.time() - orchestrator_start - response_time
                self.move_times["orchestrator"] += orchestrator_time
                
                # Handle special commands
                if response_text == "REQUEST_DRAW":
                    self.game.draw_requested = True
                    if self.log_callback:
                        await self.log_callback(f"{current_player.capitalize()} offers a draw")
                    # Switch turns without making a move
                    self.game.board.push_pass()
                    return {"player": current_player, "action": "draw_offer", "response_time": response_time}
                    
                elif response_text == "RESIGN":
                    self.game.resigned = current_player
                    self.is_running = False
                    if self.log_callback:
                        await self.log_callback(f"{current_player.capitalize()} resigns!")
                    return {"player": current_player, "action": "resign", "response_time": response_time}
                    
                elif response_text == "DRAW_ACCEPTED" and draw_requested:
                    self.game.draw_accepted = True
                    self.is_running = False
                    if self.log_callback:
                        await self.log_callback("Draw accepted!")
                    return {"player": current_player, "action": "draw_accepted", "response_time": response_time}
                    
                elif response_text == "DRAW_REFUSED" and draw_requested:
                    self.game.draw_requested = False
                    if self.log_callback:
                        await self.log_callback(f"{current_player.capitalize()} refuses the draw")
                    # Continue with a regular move by getting a new response
                    continue
                
                # Extract move (handle various formats)
                move = response_text.split()[0].lower() if response_text else ""
                
                # Validate and make move
                if move in game_state['legal_moves']:
                    success = self.game.make_move(move, response_time)
                    if success:
                        self.move_times[current_player].append(response_time)
                        
                        # Clear draw offer after a move
                        if hasattr(self.game, 'draw_requested'):
                            self.game.draw_requested = False
                        
                        # Log the move
                        if self.log_callback:
                            await self.log_callback(f"{current_player.capitalize()} plays: {move}")
                        
                        # Broadcast move
                        if self.move_callback:
                            await self.move_callback({
                                "player": current_player,
                                "move": move,
                                "fen": self.game.get_board_fen(),
                                "response_time": response_time
                            })
                        
                        # Broadcast updated state
                        if self.state_callback:
                            await self.state_callback(self.game.get_game_state())
                        
                        return {
                            "player": current_player,
                            "move": move,
                            "response_time": response_time,
                            "board_fen": self.game.get_board_fen()
                        }
                else:
                    # Invalid move - retry with error message
                    if self.log_callback:
                        await self.log_callback(f"Invalid move from {current_player}: {move}", level="warning")
                    
                    if attempt < max_retries - 1:
                        response = await self._send_invalid_move_prompt(current_agent, response, game_state, last_move)
                        # Loop will continue with new response
                    else:
                        # Max retries reached
                        if self.log_callback:
                            await self.log_callback(f"{current_player.capitalize()} failed to make valid move after {max_retries} attempts", level="error")
                        return {"error": f"Max retries reached for {current_player}", "player": current_player}
                        
            except Exception as e:
                if self.log_callback:
                    await self.log_callback(f"Error during {current_player} turn: {str(e)}", level="error")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # Brief pause before retry
                else:
                    return {"error": f"Exception during {current_player} turn: {str(e)}", "player": current_player}
    
    async def play_game(self):
        """
        Play a complete game asynchronously.
        
        This method runs the game loop until completion.
        """
        self.is_running = True
        
        if self.log_callback:
            await self.log_callback("Game started!")
        
        # Broadcast initial state
        if self.state_callback:
            await self.state_callback(self.game.get_game_state())
        
        move_count = 0
        max_moves = 200  # Prevent infinite games
        
        while self.is_running and move_count < max_moves:
            if self.game.is_game_over():
                break
                
            turn_result = await self.play_turn()
            
            if turn_result is None:
                break
                
            if "error" in turn_result:
                if self.log_callback:
                    await self.log_callback(f"Game ended due to error: {turn_result['error']}", level="error")
                break
                
            move_count += 1
            
            # Check game status
            if self.game.is_game_over():
                result = self.game.get_game_result()
                winner = self._get_winner()
                
                if self.log_callback:
                    if winner == "draw":
                        await self.log_callback(f"Game ended in a draw ({result})")
                    else:
                        await self.log_callback(f"Game over! {winner.capitalize()} wins by {result}")
                
                # Final state broadcast
                if self.state_callback:
                    final_state = self.game.get_game_state()
                    final_state['winner'] = winner
                    final_state['result'] = result
                    await self.state_callback(final_state)
                    
                break
            
            # Brief pause between moves for visibility
            await asyncio.sleep(0.5)
        
        # Handle special end conditions
        if hasattr(self.game, 'resigned') and self.game.resigned:
            winner = "black" if self.game.resigned == "white" else "white"
            if self.state_callback:
                final_state = self.game.get_game_state()
                final_state['winner'] = winner
                final_state['result'] = 'resignation'
                await self.state_callback(final_state)
                
        elif hasattr(self.game, 'draw_accepted') and self.game.draw_accepted:
            if self.state_callback:
                final_state = self.game.get_game_state()
                final_state['winner'] = 'draw'
                final_state['result'] = 'agreement'
                await self.state_callback(final_state)
        
        self.is_running = False
        
        if self.log_callback:
            await self.log_callback("Game completed!")
            await self.log_callback(f"Total moves: {move_count}")
            await self.log_callback(f"White avg time: {sum(self.move_times['white'])/len(self.move_times['white']) if self.move_times['white'] else 0:.2f}s")
            await self.log_callback(f"Black avg time: {sum(self.move_times['black'])/len(self.move_times['black']) if self.move_times['black'] else 0:.2f}s")
            await self.log_callback(f"Orchestrator total time: {self.move_times['orchestrator']:.2f}s")
    
    def pause(self):
        """Pause the game."""
        self.is_paused = True
        
    def resume(self):
        """Resume the game."""
        self.is_paused = False
        
    def stop(self):
        """Stop the game."""
        self.is_running = False
        self.is_paused = False
    
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