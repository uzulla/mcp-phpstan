"""
Main entry point for the MCP PHPStan integration.

This script provides a command-line interface for running the MCP PHPStan integration.
It handles parsing command-line arguments and running the appropriate functionality.
"""

import sys
import os
import argparse
from typing import List, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.McpIntegration.McpClient import McpClient


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="MCP PHPStan Integration - Automatically fix PHPStan errors with Claude Code"
    )
    
    # Required arguments
    parser.add_argument(
        "project_path",
        help="Path to the PHP project to analyze"
    )
    
    # PHPStan options
    phpstan_group = parser.add_argument_group("PHPStan Options")
    phpstan_group.add_argument(
        "--paths", "-p",
        nargs="+",
        help="Paths to analyze (defaults to paths in phpstan.neon)"
    )
    phpstan_group.add_argument(
        "--level", "-l",
        type=int,
        help="PHPStan rule level (0-9, defaults to level in phpstan.neon)"
    )
    phpstan_group.add_argument(
        "--config", "-c",
        help="Path to PHPStan config file (defaults to phpstan.neon in project root)"
    )
    phpstan_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Run PHPStan in verbose mode"
    )
    
    # MCP options
    mcp_group = parser.add_argument_group("MCP Options")
    mcp_group.add_argument(
        "--max-errors", "-m",
        type=int,
        default=3,
        help="Maximum errors per batch (default: 3)"
    )
    mcp_group.add_argument(
        "--max-iterations", "-i",
        type=int,
        default=10,
        help="Maximum iterations to run (default: 10)"
    )
    mcp_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without applying fixes (for testing)"
    )
    
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    # Parse command-line arguments
    args = parse_args()
    
    # Initialize MCP client
    client = McpClient(
        args.project_path,
        max_errors_per_batch=args.max_errors
    )
    
    # If dry run, just analyze and print
    if args.dry_run:
        print("Running in dry-run mode (no fixes will be applied)")
        
        # Run PHPStan analysis
        output, return_code, batches = client.run_phpstan_analysis(
            args.paths,
            args.level,
            args.config,
            args.verbose
        )
        
        # Print results
        if return_code == 0:
            print("No PHPStan errors found")
            return 0
        
        print(f"Found {sum(batch['batch']['batch_size'] for batch in batches)} errors in {len(batches)} batches")
        
        # Print first batch as example
        if batches:
            print("\nExample batch:")
            for file_path, errors in batches[0]["errors_by_file"].items():
                print(f"\nFile: {file_path}")
                for error in errors:
                    print(f"  Line {error['line']}: {error['message']}")
        
        return 1
    
    # Process PHPStan errors
    success = client.process_phpstan_errors(
        args.paths,
        args.level,
        args.config,
        args.verbose,
        args.max_iterations
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
