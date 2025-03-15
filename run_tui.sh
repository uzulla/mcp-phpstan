#!/bin/bash

# Run the TUI interface for MCP PHPStan Integration

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found."
    echo "Please create a .env file by copying .env.example:"
    echo ""
    echo "    cp .env.example .env"
    echo ""
    echo "Then edit the .env file and add your Claude API key:"
    echo ""
    echo "    CLAUDE_API_KEY=your_api_key_here"
    echo ""
    exit 1
fi

# Check if CLAUDE_API_KEY is set
if [ -z "$CLAUDE_API_KEY" ]; then
    echo "Error: CLAUDE_API_KEY environment variable not set."
    echo "Your .env file exists but may not contain the API key."
    echo "Please add the following line to your .env file:"
    echo ""
    echo "    CLAUDE_API_KEY=your_api_key_here"
    echo ""
    echo "Or set it before running this script:"
    echo ""
    echo "    export CLAUDE_API_KEY=your_api_key_here"
    echo ""
    exit 1
fi

# Check if a project path was provided
if [ -z "$1" ]; then
    echo "Error: No project path provided."
    echo "Usage: $0 /path/to/php/project [options]"
    echo ""
    echo "Options:"
    echo "  --max-errors N    Maximum errors per batch (default: 3)"
    echo "  --max-iterations N    Maximum iterations (default: 10)"
    echo "  --simple    Use simple CLI interface instead of TUI"
    echo "  --verbose    Run in verbose mode"
    exit 1
fi

# Parse arguments
PROJECT_PATH="$1"
shift

MAX_ERRORS=3
MAX_ITERATIONS=10
USE_SIMPLE=false
VERBOSE=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --max-errors)
            MAX_ERRORS="$2"
            shift 2
            ;;
        --max-iterations)
            MAX_ITERATIONS="$2"
            shift 2
            ;;
        --simple)
            USE_SIMPLE=true
            shift
            ;;
        --verbose)
            VERBOSE="--verbose"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if project path exists
if [ ! -d "$PROJECT_PATH" ]; then
    echo "Error: Project path does not exist: $PROJECT_PATH"
    exit 1
fi

# Run the appropriate interface
if [ "$USE_SIMPLE" = true ]; then
    echo "Running simple CLI interface..."
    python3 src/TuiInterface/simple_client.py "$PROJECT_PATH" --max-errors "$MAX_ERRORS" --max-iterations "$MAX_ITERATIONS" $VERBOSE
else
    echo "Running TUI interface..."
    python3 src/TuiInterface/tui_client.py "$PROJECT_PATH" --max-errors "$MAX_ERRORS" --max-iterations "$MAX_ITERATIONS"
fi
