"""
Web server for the Chess LLM Orchestration System using FastAPI
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import asyncio
from typing import Dict, Any, Optional
from chess_llm.game import ChessGame
from chess_llm.async_orchestrator import AsyncGameOrchestrator
import random
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Chess LLM Orchestration System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active games and connections
active_connections: Dict[str, WebSocket] = {}
games: Dict[str, ChessGame] = {}
orchestrators: Dict[str, AsyncGameOrchestrator] = {}
game_tasks: Dict[str, asyncio.Task] = {}

# Request models
class StartGameRequest(BaseModel):
    white_provider: Optional[str] = None
    white_model: Optional[str] = None
    black_provider: Optional[str] = None
    black_model: Optional[str] = None

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")
# Also mount img directory at /img for chessboard.js compatibility
app.mount("/img", StaticFiles(directory="static/img"), name="img")

@app.get("/")
async def get_homepage():
    """Serve the main HTML page."""
    return FileResponse("static/index.html")

@app.get("/favicon.ico")
async def favicon():
    """Return a 204 No Content for favicon requests to avoid 404 errors."""
    from fastapi import Response
    return Response(status_code=204)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for real-time updates."""
    await websocket.accept()
    
    # Assign a unique ID to this connection
    connection_id = str(id(websocket))
    active_connections[connection_id] = websocket
    
    try:
        # Send initial game state if a game exists
        if games:
            game_id = list(games.keys())[0]
            game = games[game_id]
            await websocket.send_text(json.dumps({
                "type": "game_state",
                "fen": game.get_board_fen(),
                "current_player": game.get_current_player(),
                "game_over": game.is_game_over(),
                "move_count": len(game.game_history)
            }))
        
        while True:
            # Keep the connection alive
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        # Remove the connection when client disconnects
        if connection_id in active_connections:
            del active_connections[connection_id]

@app.get("/api/game/state")
async def get_game_state():
    """Get current game state."""
    if not games:
        # Create a default game if none exists
        games["default"] = ChessGame()
    
    game_id = list(games.keys())[0]
    game = games[game_id]
    
    return game.get_game_state()

@app.post("/api/game/move/{move}")
async def make_move(move: str):
    """Make a move in the current game."""
    if not games:
        games["default"] = ChessGame()
    
    game_id = list(games.keys())[0]
    game = games[game_id]
    
    success = game.make_move(move)
    
    if success:
        # Broadcast updated game state to all connected clients
        await broadcast_game_state(game)
        return {"success": True, "new_state": game.get_game_state()}
    else:
        return {"success": False, "error": "Invalid move"}

@app.post("/api/game/reset")
async def reset_game():
    """Reset the current game."""
    if not games:
        # Create a new game
        game_id = "default"
        games[game_id] = ChessGame()
    else:
        game_id = list(games.keys())[0]
        games[game_id].reset_game()
    
    game = games[game_id]
    
    # Broadcast updated game state to all connected clients
    await broadcast_game_state(game)
    
    return {"success": True, "new_state": game.get_game_state()}

async def broadcast_game_state(game: ChessGame):
    """Broadcast game state to all active WebSocket connections."""
    game_state = game.get_game_state()
    
    # Remove disconnected clients
    disconnected = []
    for connection_id, websocket in active_connections.items():
        try:
            await websocket.send_text(json.dumps({
                "type": "game_state",
                **game_state
            }))
        except WebSocketDisconnect:
            disconnected.append(connection_id)
    
    # Clean up disconnected clients
    for connection_id in disconnected:
        del active_connections[connection_id]

async def broadcast_log(message: str, level: str = "info"):
    """Broadcast log message to all active WebSocket connections."""
    # Remove disconnected clients
    disconnected = []
    for connection_id, websocket in active_connections.items():
        try:
            await websocket.send_text(json.dumps({
                "type": "log",
                "message": message,
                "level": level
            }))
        except WebSocketDisconnect:
            disconnected.append(connection_id)
    
    # Clean up disconnected clients
    for connection_id in disconnected:
        del active_connections[connection_id]

@app.post("/api/game/start")
async def start_llm_game(request: StartGameRequest):
    """Start a new LLM vs LLM game."""
    game_id = "default"  # For now, single game support
    
    # Stop any existing game
    if game_id in game_tasks:
        if not game_tasks[game_id].done():
            orchestrators[game_id].stop()
            game_tasks[game_id].cancel()
    
    # Create new game and orchestrator
    games[game_id] = ChessGame()
    orchestrator = AsyncGameOrchestrator(game_id=game_id)
    orchestrator.game = games[game_id]  # Use the same game instance
    orchestrators[game_id] = orchestrator
    
    # Set up callbacks for real-time updates
    async def move_callback(move_data):
        await broadcast_game_state(games[game_id])
    
    async def log_callback(message, level="info"):
        await broadcast_log(message, level)
    
    async def state_callback(state):
        # Broadcast state updates
        await broadcast_game_state(games[game_id])
    
    orchestrator.set_callbacks(move_callback, log_callback, state_callback)
    
    # Default LLM selection if not provided
    available_providers = {
        "openai": ["gpt-4", "gpt-3.5", "gpt-4o"],
        "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        "qwen": ["qwen-max", "qwen-plus"],
        "mock": ["mock"]  # Add mock provider
    }
    
    # Check for API keys and use mock if none available
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_qwen = bool(os.getenv("ALIBABA_CLOUD_API_KEY"))
    
    # If no API keys are set, use mock agents
    if not (has_openai or has_anthropic or has_qwen):
        request.white_provider = "mock"
        request.white_model = "mock"
        request.black_provider = "mock"
        request.black_model = "mock"
        await broadcast_log("No API keys found, using mock agents for testing", level="warning")
    else:
        # Select from available providers based on API keys
        available = []
        if has_openai:
            available.append("openai")
        if has_anthropic:
            available.append("anthropic")
        if has_qwen:
            available.append("qwen")
            
        # Select random providers if not specified
        if not request.white_provider and available:
            request.white_provider = random.choice(available)
            request.white_model = random.choice(available_providers[request.white_provider])
        elif not request.white_provider:
            request.white_provider = "mock"
            request.white_model = "mock"
        
        if not request.black_provider and available:
            request.black_provider = random.choice(available)
            request.black_model = random.choice(available_providers[request.black_provider])
        elif not request.black_provider:
            request.black_provider = "mock"
            request.black_model = "mock"
    
    try:
        # Initialize agents
        await orchestrator.setup_agents(
            request.white_provider, request.white_model,
            request.black_provider, request.black_model
        )
        
        await broadcast_log(f"Starting game: {request.white_provider}/{request.white_model} (White) vs {request.black_provider}/{request.black_model} (Black)")
        
        # Start game in background
        game_task = asyncio.create_task(orchestrator.play_game())
        game_tasks[game_id] = game_task
        
        return {
            "success": True,
            "game_id": game_id,
            "white": f"{request.white_provider}/{request.white_model}",
            "black": f"{request.black_provider}/{request.black_model}"
        }
        
    except Exception as e:
        await broadcast_log(f"Failed to start game: {str(e)}", level="error")
        return {"success": False, "error": str(e)}

@app.post("/api/game/pause")
async def pause_game():
    """Pause the current game."""
    game_id = "default"
    
    if game_id in orchestrators:
        orchestrators[game_id].pause()
        await broadcast_log("Game paused")
        return {"success": True}
    else:
        return {"success": False, "error": "No active game"}

@app.post("/api/game/resume")
async def resume_game():
    """Resume the current game."""
    game_id = "default"
    
    if game_id in orchestrators:
        orchestrators[game_id].resume()
        await broadcast_log("Game resumed")
        return {"success": True}
    else:
        return {"success": False, "error": "No active game"}

@app.post("/api/game/stop")
async def stop_game():
    """Stop the current game."""
    game_id = "default"
    
    if game_id in orchestrators:
        orchestrators[game_id].stop()
        if game_id in game_tasks:
            game_tasks[game_id].cancel()
        await broadcast_log("Game stopped")
        return {"success": True}
    else:
        return {"success": False, "error": "No active game"}

if __name__ == "__main__":
    import uvicorn
    
    # Create a default game
    games["default"] = ChessGame()
    
    print("Starting Chess LLM Orchestration System web server...")
    print("Visit http://localhost:8000 to view the chess board")
    
    uvicorn.run(app, host="127.0.0.1", port=8000)