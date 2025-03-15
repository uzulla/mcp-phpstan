#!/usr/bin/env python3
"""
Simple CLI interface for MCP PHPStan Integration.

This module provides a simple command-line interface for the MCP PHPStan Integration tool.
It's designed to be used in environments where the TUI doesn't work well.
"""

import os
import sys
import json
import argparse
import time
import dotenv
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.McpIntegration.McpClient import McpClient
from src.PhpStanRunner.Runner import PhpStanRunner

# Load environment variables from .env file if it exists
dotenv.load_dotenv()


class SimpleClient:
    """Simple CLI interface for MCP PHPStan Integration."""

    def __init__(self, 
                 project_path: str,
                 max_errors_per_batch: int = 3,
                 max_iterations: int = 10,
                 verbose: bool = False):
        """
        Initialize the simple CLI interface.
        
        Args:
            project_path: Path to the PHP project
            max_errors_per_batch: Maximum number of errors to process in a single batch
            max_iterations: Maximum number of iterations to run
            verbose: Whether to run in verbose mode
        """
        self.project_path = os.path.abspath(project_path)
        self.max_errors_per_batch = max_errors_per_batch
        self.max_iterations = max_iterations
        self.verbose = verbose
        
        # Check if Claude API key is set
        if not os.environ.get("CLAUDE_API_KEY"):
            print("Error: CLAUDE_API_KEY environment variable not set.")
            print("Please set it in .env file or as an environment variable.")
            sys.exit(1)
        
        # Initialize MCP client
        self.mcp_client = McpClient(self.project_path, self.max_errors_per_batch)
        
        # Initialize PHPStan runner
        self.phpstan_runner = PhpStanRunner(self.project_path)
        
        # Initialize log
        self.log = []

    def add_log(self, message: str):
        """
        Add a message to the log.
        
        Args:
            message: Message to add to the log
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log.append(log_entry)
        print(log_entry)

    def run_phpstan_analysis(self, 
                            paths: Optional[List[str]] = None,
                            level: Optional[int] = None,
                            config_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Run PHPStan analysis and format the errors.
        
        Args:
            paths: List of paths to analyze
            level: PHPStan rule level (0-9)
            config_path: Path to PHPStan config file
            
        Returns:
            List of formatted error batches
        """
        self.add_log(f"Running PHPStan analysis on {self.project_path}...")
        
        # Run PHPStan analysis
        output, return_code, batches = self.mcp_client.run_phpstan_analysis(
            paths, level, config_path, self.verbose
        )
        
        # Log the results
        if return_code == 0:
            self.add_log("No PHPStan errors found!")
            return []
        
        self.add_log(f"Found {sum(len(batch['errors_by_file'][file]) for batch in batches for file in batch['errors_by_file'])} errors in {len(batches)} batches.")
        
        return batches

    def fix_batch(self, batch: Dict[str, Any]) -> bool:
        """
        Fix a batch of errors using Claude.
        
        Args:
            batch: Batch of errors to fix
            
        Returns:
            True if fixes were applied successfully, False otherwise
        """
        batch_idx = batch["batch"]["index"]
        total_batches = batch["batch"]["total"]
        
        self.add_log(f"Processing batch {batch_idx + 1}/{total_batches}...")
        
        # Prepare MCP message
        message = self.mcp_client.prepare_mcp_message(batch)
        
        # Send to Claude
        self.add_log("Sending errors to Claude...")
        response = self.mcp_client.send_to_claude(message)
        
        # Check if Claude returned an error
        if response.get("status") == "error":
            self.add_log(f"Error from Claude: {response.get('message')}")
            return False
        
        # Apply fixes
        if "fixes" in response and response["fixes"]:
            self.add_log(f"Applying {len(response['fixes'])} fixes suggested by Claude...")
            success = self.mcp_client.apply_fixes(response["fixes"])
            
            if success:
                self.add_log("Fixes applied successfully!")
                return True
            else:
                self.add_log("Failed to apply fixes.")
                return False
        else:
            self.add_log("No fixes suggested by Claude.")
            return False

    def fix_all_batches(self, batches: List[Dict[str, Any]]) -> bool:
        """
        Fix all batches of errors.
        
        Args:
            batches: List of batches to fix
            
        Returns:
            True if all batches were fixed successfully, False otherwise
        """
        if not batches:
            self.add_log("No errors to fix!")
            return True
        
        self.add_log(f"Fixing {len(batches)} batches of errors...")
        
        iteration = 0
        while iteration < self.max_iterations and batches:
            self.add_log(f"\nIteration {iteration + 1}/{self.max_iterations}")
            
            # Fix each batch
            for batch in batches:
                self.fix_batch(batch)
            
            # Run PHPStan again to check if all errors are fixed
            batches = self.run_phpstan_analysis()
            
            if not batches:
                self.add_log("All errors fixed!")
                return True
            
            iteration += 1
        
        if batches:
            self.add_log(f"Reached maximum iterations ({self.max_iterations}) without fixing all errors.")
            return False
        
        return True

    def run(self, 
           paths: Optional[List[str]] = None,
           level: Optional[int] = None,
           config_path: Optional[str] = None) -> bool:
        """
        Run the simple CLI interface.
        
        Args:
            paths: List of paths to analyze
            level: PHPStan rule level (0-9)
            config_path: Path to PHPStan config file
            
        Returns:
            True if all errors were fixed, False otherwise
        """
        self.add_log(f"Starting MCP PHPStan Integration for {self.project_path}")
        
        # Run PHPStan analysis
        batches = self.run_phpstan_analysis(paths, level, config_path)
        
        # If no errors, we're done
        if not batches:
            return True
        
        # Fix all batches
        return self.fix_all_batches(batches)


def main():
    """Main entry point for the simple CLI interface."""
    parser = argparse.ArgumentParser(description="Simple CLI interface for MCP PHPStan Integration")
    parser.add_argument("project_path", help="Path to the PHP project")
    parser.add_argument("--paths", "-p", nargs="+", help="Paths to analyze")
    parser.add_argument("--level", "-l", type=int, help="PHPStan rule level (0-9)")
    parser.add_argument("--config", "-c", help="Path to PHPStan config file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Run in verbose mode")
    parser.add_argument("--max-errors", "-m", type=int, default=3, help="Maximum errors per batch")
    parser.add_argument("--max-iterations", "-i", type=int, default=10, help="Maximum iterations")
    
    args = parser.parse_args()
    
    # Initialize simple CLI interface
    client = SimpleClient(
        args.project_path,
        args.max_errors,
        args.max_iterations,
        args.verbose
    )
    
    # Run the interface
    success = client.run(args.paths, args.level, args.config)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
