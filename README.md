# Chess LLM Orchestration System

An orchestration system that pits different LLMs against each other in chess games. The system uses YAML configuration to define LLM providers and models, with a controller that manages game flow between agents. Currently supports OpenAI, Anthropic, Qwen (Alibaba Cloud), and OpenRouter providers.

## Features

- **Multi-Provider LLM Support**: Configure different LLM providers (OpenAI, Anthropic, Qwen/Alibaba Cloud, OpenRouter, etc.)
- **Dynamic Agent Assignment**: Randomly assign LLMs to white/black pieces for each game
- **Real-time Visualization**: Web interface with chessboard visualization
- **Game State Management**: Complete chess game logic with move validation
- **Timing Mechanism**: Track response times for each move
- **Referee System**: Controller LLM validates moves and game state

## Project Structure

```
chess-llm/
├── chess_llm/
│   ├── __init__.py
│   ├── game.py           # Chess game logic
│   ├── agents.py         # LLM agent communication
│   ├── orchestrator.py   # Game flow management
│   ├── main.py           # Main application entry point
│   └── web/
│       └── server.py     # Web server with FastAPI
├── static/               # Web frontend files
│   └── index.html        # Main HTML interface
├── venv/                 # Python virtual environment
├── requirements.txt      # Python dependencies
├── llm_config.yaml       # LLM configuration
├── .env.sample           # Sample environment variables
├── start.sh              # Startup script
└── test_chess.py         # Chess game logic tests
```

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd chess-llm
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables for LLM API keys:
   ```bash
   # Copy the sample file and update with your actual API keys
   cp .env.sample .env
   # Then edit .env with your actual API keys
   
   # Or set them directly in your shell:
   export OPENAI_API_KEY="your-openai-api-key"
   export ANTHROPIC_API_KEY="your-anthropic-api-key"
   export ALIBABA_CLOUD_API_KEY="your-alibaba-cloud-api-key"
   # Add other provider keys as needed
   ```

## Usage

### Starting the Web Interface

Run the startup script to start the web server:
```bash
./start.sh
```

Then visit `http://localhost:8000` in your browser to view the chess board.

### Running a Game

The system can be run in different modes:

1. **Web Interface Mode**: Play through the web interface with real-time visualization
2. **CLI Mode**: Run games directly from the command line
3. **LLM vs LLM Mode**: Automatically play games between different LLMs

### Configuration

The `llm_config.yaml` file contains configuration for:
- LLM providers and their API settings
- Available models for each provider
- Agent-specific instructions
- Referee/controller LLM settings

## Development

### Running Tests

Test the chess game logic:
```bash
python test_chess.py
```

### Code Structure

- **Game Logic**: Implemented using the `python-chess` library
- **Web Server**: Built with FastAPI for real-time updates
- **Frontend**: Uses chessboard.js for chess board visualization
- **LLM Integration**: Supports multiple providers through their respective SDKs

## Requirements

- Python 3.7+
- Virtual environment (recommended)
- API keys for LLM providers you want to use

## License

This project is licensed under the MIT License.