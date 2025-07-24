# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based chess orchestration system that enables different Large Language Models (LLMs) to play chess against each other. The system uses FastAPI for the web server, python-chess for game logic, and supports multiple LLM providers including OpenAI, Anthropic, Qwen (Alibaba Cloud), and OpenRouter.

## Common Development Commands

### Setup and Installation
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (API keys)
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export ALIBABA_CLOUD_API_KEY="your-key"
```

### Running the Application
```bash
# Start the web server (recommended)
./start.sh

# Or run directly
python3 -m chess_llm.web.server
```

The web interface will be available at http://localhost:8000

### Testing
```bash
# Run chess game logic tests
python test_chess.py

# Run orchestrator tests
python test_orchestrator.py

# Run a specific test
python test_chess.py -k test_name
```

## Architecture Overview

### Core Components

1. **Game Logic (chess_llm/game.py)**
   - Manages chess game state using python-chess library
   - Handles move validation, game rules, and state tracking
   - Provides methods for move execution and game status checks

2. **LLM Agent System (chess_llm/agents.py)**
   - Abstract base class for LLM agents with provider-specific implementations
   - Handles communication with different LLM APIs (OpenAI, Anthropic, Qwen, OpenRouter)
   - Manages prompt formatting and response parsing for chess moves

3. **Orchestrator (chess_llm/orchestrator.py)**
   - Controls game flow between LLM agents
   - Manages turn-taking, move validation, and game termination
   - Implements retry logic and error handling for LLM responses

4. **Web Server (chess_llm/web/server.py)**
   - FastAPI application providing WebSocket and HTTP endpoints
   - Real-time game state updates via WebSocket
   - RESTful API for game control and status

### Configuration System

The application uses a YAML-based configuration system (`llm_config.yaml`) that defines:
- LLM provider credentials and endpoints
- Model-specific parameters (temperature, max_tokens, etc.)
- Agent behavior customization
- Referee/controller LLM selection

### Frontend Architecture

The web interface (`static/index.html`) uses:
- chessboard.js for interactive chess board visualization
- WebSocket connection for real-time game updates
- Vanilla JavaScript for UI interactions

## Key Development Patterns

1. **LLM Communication**: All LLM interactions go through the agent abstraction layer, allowing easy addition of new providers
2. **Game State Management**: The game state is centrally managed and broadcast to all connected clients
3. **Error Handling**: Robust retry mechanisms for LLM API failures with configurable timeouts
4. **Logging**: Comprehensive JSON logging in the `logs/` directory for debugging and analysis

## Important Notes

- The `.env.sample` file mentioned in README.md does not exist - API keys must be set as environment variables
- No linting or code formatting configuration exists - follow PEP 8 conventions
- The `agents/`, `controllers/`, and `utils/` directories are empty placeholders
- Test files use basic assertions without a formal testing framework like pytest