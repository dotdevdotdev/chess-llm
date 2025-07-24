"""
Web server for the Chess LLM Orchestration System using FastAPI
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from typing import Dict, Any
from chess_llm.game import ChessGame

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

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_homepage():
    """Serve the main HTML page."""
    return FileResponse("static/index.html")

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

if __name__ == "__main__":
    import uvicorn
    
    # Create a default game
    games["default"] = ChessGame()
    
    print("Starting Chess LLM Orchestration System web server...")
    print("Visit http://localhost:8000 to view the chess board")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)