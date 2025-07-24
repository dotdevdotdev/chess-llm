#!/bin/bash

# Start the Chess LLM Orchestration System

# Activate virtual environment
source venv/bin/activate

# Start the web server
python3 -m chess_llm.web.server