#!/bin/bash

# Claude Code MCP command handler for PHPStan Integration

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

# Check if a command was provided
if [ -z "$1" ]; then
    echo "Error: No command provided."
    echo "Usage: $0 <command> [--project-path /path/to/php/project] [--args '{\"key\": \"value\"}']"
    echo ""
    echo "Commands:"
    echo "  run_phpstan    Run PHPStan analysis on a PHP project"
    echo "  fix_errors     Fix errors detected by PHPStan"
    echo "  list_errors    List errors detected by PHPStan"
    echo "  select_errors  Select specific errors to fix"
    echo ""
    echo "Example:"
    echo "  $0 run_phpstan --project-path /path/to/php/project"
    echo "  $0 fix_errors --project-path /path/to/php/project --args '{\"batch_index\": 0}'"
    exit 1
fi

# Parse arguments
COMMAND="$1"
shift

PROJECT_PATH=""
ARGS="{}"

while [ "$#" -gt 0 ]; do
    case "$1" in
        --project-path)
            PROJECT_PATH="$2"
            shift 2
            ;;
        --args)
            ARGS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if project path was provided
if [ -z "$PROJECT_PATH" ]; then
    echo "Error: No project path provided."
    echo "Usage: $0 <command> --project-path /path/to/php/project [--args '{\"key\": \"value\"}']"
    exit 1
fi

# Check if project path exists
if [ ! -d "$PROJECT_PATH" ]; then
    echo "Error: Project path does not exist: $PROJECT_PATH"
    exit 1
fi

# Run the MCP command handler
python3 src/ClaudeCodeMcp/mcp_command.py --project-path "$PROJECT_PATH" --command "$COMMAND" --args "$ARGS"
