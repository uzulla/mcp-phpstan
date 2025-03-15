"""
MCP Command Handler for Claude Code

This module provides the command handler for Claude Code MCP commands.
It allows Claude Code to interact with the PHPStan integration via MCP.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional, Tuple

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ClaudeCodeMcp.claude_code_mcp import ClaudeCodeMcpHandler


def handle_mcp_command(command: str, args: Dict[str, Any], project_path: str) -> Dict[str, Any]:
    """
    Handle an MCP command from Claude Code.
    
    Args:
        command: Command to handle
        args: Command arguments
        project_path: Path to the PHP project
        
    Returns:
        Response to the command
    """
    # Initialize handler
    handler = ClaudeCodeMcpHandler(project_path)
    
    # Handle command
    return handler.handle_command(command, args)


def main():
    """Main entry point for the MCP command handler."""
    parser = argparse.ArgumentParser(description="MCP command handler for Claude Code")
    parser.add_argument("--project-path", "-p", required=True, help="Path to the PHP project")
    parser.add_argument("--command", "-c", required=True, help="Command to handle")
    parser.add_argument("--args", "-a", help="JSON-encoded command arguments")
    
    args = parser.parse_args()
    
    # Parse command arguments
    command_args = {}
    if args.args:
        try:
            command_args = json.loads(args.args)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in command arguments: {args.args}")
            sys.exit(1)
    
    # Handle command
    response = handle_mcp_command(args.command, command_args, args.project_path)
    
    # Print response as JSON
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    main()
