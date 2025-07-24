"""
Main application for the Chess LLM Orchestration System
"""
import argparse
import os
import sys
import asyncio
from chess_llm.orchestrator import GameOrchestrator


def main():
    parser = argparse.ArgumentParser(description="Chess LLM Orchestration System")
    parser.add_argument("--white-provider", default="openai", 
                        help="Provider for white player (default: openai)")
    parser.add_argument("--white-model", default="gpt-4", 
                        help="Model for white player (default: gpt-4)")
    parser.add_argument("--black-provider", default="anthropic", 
                        help="Provider for black player (default: anthropic)")
    parser.add_argument("--black-model", default="claude-3-opus", 
                        help="Model for black player (default: claude-3-opus)")
    parser.add_argument("--max-turns", type=int, default=100,
                        help="Maximum number of turns (default: 100)")
    parser.add_argument("--config", default="llm_config.yaml",
                        help="Path to configuration file (default: llm_config.yaml)")
    parser.add_argument("--web", action="store_true",
                        help="Start web server instead of playing a game")
    
    args = parser.parse_args()
    
    # Check if API keys are set
    required_env_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY"
    ]
    
    missing_keys = [var for var in required_env_vars if not os.getenv(var)]
    if missing_keys:
        print("Warning: The following required environment variables are not set:")
        for key in missing_keys:
            print(f"  - {key}")
        print("\nPlease set these environment variables to run the full application.")
        print("You can still test the game logic without API keys.")
        # We'll continue anyway to allow testing
    
    if args.web:
        # Start web server
        print("Starting Chess LLM Orchestration System web server...")
        try:
            from chess_llm.web.server import app
            import uvicorn
            uvicorn.run(app, host="0.0.0.0", port=8000)
        except Exception as e:
            print(f"Error starting web server: {e}")
            return
    else:
        # Play a game
        print("Initializing Chess LLM Orchestration System...")
        orchestrator = GameOrchestrator(args.config)
        
        try:
            orchestrator.setup_agents(
                args.white_provider, args.white_model,
                args.black_provider, args.black_model
            )
            print(f"Agents set up successfully:")
            print(f"  White: {args.white_provider}/{args.white_model}")
            print(f"  Black: {args.black_provider}/{args.black_model}")
        except Exception as e:
            print(f"Error setting up agents: {e}")
            print("Continuing with game logic testing only...")
        
        # Play game
        print("\nStarting game...")
        try:
            results = orchestrator.play_game(args.max_turns)
            
            # Display results
            game_state = results["game_state"]
            print("\nGame completed!")
            print(f"Final board: {game_state['fen']}")
            print(f"Game over: {game_state['game_over']}")
            if game_state['result']:
                print(f"Result: {game_state['result']}")
            if results["winner"]:
                print(f"Winner: {results['winner']}")
            
            print(f"\nGame log:")
            for i, log_entry in enumerate(results["game_log"]):
                if "error" in log_entry:
                    print(f"  Turn {i+1}: ERROR - {log_entry['error']}")
                else:
                    print(f"  Turn {i+1}: {log_entry['player']} played {log_entry['move']} "
                          f"(took {log_entry['response_time']:.2f}s) - {log_entry['validation']}")
            
            # Show move times statistics
            white_times = results["move_times"]["white"]
            black_times = results["move_times"]["black"]
            if white_times:
                avg_white = sum(white_times) / len(white_times)
                print(f"\nWhite average response time: {avg_white:.2f}s")
            if black_times:
                avg_black = sum(black_times) / len(black_times)
                print(f"Black average response time: {avg_black:.2f}s")
                
        except KeyboardInterrupt:
            print("\nGame interrupted by user.")
        except Exception as e:
            print(f"Error during game: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()