# Chess LLM Implementation Task Prompt

## Context
You are tasked with implementing missing features in a Chess LLM Orchestration System. This system allows different Large Language Models (LLMs) to play chess against each other with a web-based interface for visualization.

## Current State
The codebase has a solid foundation with:
- Chess game logic (using python-chess)
- LLM agent abstractions for OpenAI, Anthropic, and Qwen
- Web server with WebSocket support (FastAPI + uvicorn)
- Frontend with chessboard.js visualization
- Configuration system (YAML-based)

**CRITICAL GAP**: The web server and game orchestrator are not connected. The "Start LLM Game" button doesn't actually start an LLM game.

## Your Mission
Implement all missing features to make the app fully functional, allowing:
1. Two LLM agents to play chess against each other
2. Real-time move updates via WebSocket
3. Game orchestration with move validation
4. Score keeping and timing (with separate clocks for white/black/orchestrator)
5. Error handling and recovery

## Key Game Mechanics (from PROJECT-SPEC.md)
- **Move Protocol**: LLMs can respond with: valid move, 'REQUEST_DRAW', 'RESIGN', 'DRAW_ACCEPTED', or 'DRAW_REFUSED'
- **Time Tracking**: Separate clocks for white, black, and orchestrator processing
- **Invalid Move Handling**: Send standardized "invalid response" prompt back to LLM
- **Game End Conditions**: Checkmate, stalemate, draw agreement, resignation, or time out

## Working Instructions

### 1. Initial Setup
Before starting any task:
```bash
# Start the development server
cd /Users/dotdev/projects/chess-llm
./start.sh
```

### 2. Review Process
For each work session:
1. List all project files: `find . -type f -name "*.py" -o -name "*.html" -o -name "*.md" | grep -v venv | sort`
2. Read `PROJECT-SPEC.md` to understand the complete product vision and requirements
3. Read `TASKS.md` to check current progress
4. Use MCP browse tools to visit `http://localhost:8000` and test current functionality
5. Identify the next task to work on

### 3. Implementation Guidelines
- **Test after each change**: Use MCP browse tools to verify functionality
- **Update TASKS.md**: Mark tasks complete and add notes after each implementation
- **Maintain backward compatibility**: Don't break existing features
- **Follow existing patterns**: Match the code style and architecture
- **Add error handling**: Every LLM call should have retry logic and timeout handling

### 4. Key Files to Understand
- `PROJECT-SPEC.md` - Complete product specification with detailed requirements
- `chess_llm/orchestrator.py` - Game orchestration logic (CLI-only currently)
- `chess_llm/web/server.py` - Web server (needs game integration)
- `chess_llm/agents.py` - LLM agent implementations
- `static/index.html` - Frontend interface
- `llm_config.yaml` - Configuration for LLM providers

### 5. Testing Protocol
After implementing each feature:
1. Test the specific functionality via the web UI
2. Check WebSocket messages in browser console
3. Verify error cases (e.g., invalid moves, API failures)
4. Update TASKS.md with test results

### 6. Priority Order
Focus on these critical path items first:
1. Connect web server to orchestrator (enable "Start LLM Game")
2. Implement WebSocket move streaming
3. Add error handling and retry logic
4. Complete remaining UI controls

## Technical Requirements

### API Keys
Ensure these environment variables are set:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `ALIBABA_CLOUD_API_KEY`

### Dependencies
All required packages are in `requirements.txt`. Key ones:
- `fastapi` - Web framework
- `uvicorn[standard]` - ASGI server with WebSocket support
- `python-chess` - Chess logic
- `openai` - OpenAI API client
- `anthropic` - Anthropic API client

### Architecture Constraints
- Use async/await for all LLM calls and long-running operations
- Maintain WebSocket connection for real-time updates
- Keep game state in memory (no database required for MVP)
- Use existing ChessGame class for game logic
- Follow the agent abstraction pattern for new providers

## Success Criteria
The implementation is complete when:
1. Users can click "Start LLM Game" and see two LLMs play chess
2. Moves appear in real-time on the board
3. Game completes with a winner or draw
4. Errors are handled gracefully
5. All buttons (Reset, Pause) work as expected
6. Move times and game statistics are displayed

## Important Notes
- The orchestrator currently works in CLI mode - you need to adapt it for async web operation
- WebSocket support is installed (`uvicorn[standard]`)
- The frontend is already set up to receive WebSocket messages
- Configuration for LLM providers is in `llm_config.yaml`
- Don't modify the chess game logic - it's already complete
- Focus on the integration layer between web server and game orchestrator

## Getting Help
- Read existing code carefully - patterns are established
- Check `PROJECT-SPEC.md` for complete product requirements and game rules
- Check `CLAUDE.md` for project-specific guidelines
- Use MCP tools to explore and test
- The README.md has additional context about the project goals

Begin by reading PROJECT-SPEC.md to understand the product vision, then TASKS.md to check progress, and finally review the current state of the application at http://localhost:8000.