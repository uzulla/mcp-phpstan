"""
MCP (Multi-agent Conversation Protocol) Client for PHPStan Integration

This module provides functionality to integrate PHPStan with Claude Code via MCP.
It handles sending PHPStan errors to Claude and processing the responses.
"""

import json
import os
import sys
import time
from typing import Dict, List, Optional, Any, Tuple

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.PhpStanRunner.Runner import PhpStanRunner, run_phpstan
from src.ErrorFormatter.Formatter import PhpStanErrorFormatter, format_phpstan_output


class McpClient:
    """Client for interacting with Claude Code via MCP."""

    def __init__(self, 
                 project_path: str, 
                 max_errors_per_batch: int = 3,
                 phpstan_binary: Optional[str] = None):
        """
        Initialize the MCP client.
        
        Args:
            project_path: Path to the PHP project
            max_errors_per_batch: Maximum number of errors to process in a single batch
            phpstan_binary: Path to the PHPStan binary
        """
        self.project_path = os.path.abspath(project_path)
        self.max_errors_per_batch = max_errors_per_batch
        
        # Initialize PHPStan runner
        self.phpstan_runner = PhpStanRunner(project_path, phpstan_binary)
        
        # Initialize error formatter
        self.error_formatter = PhpStanErrorFormatter(max_errors_per_batch)

    def run_phpstan_analysis(self, 
                            paths: Optional[List[str]] = None,
                            level: Optional[int] = None,
                            config_path: Optional[str] = None,
                            verbose: bool = False) -> Tuple[str, int, List[Dict[str, Any]]]:
        """
        Run PHPStan analysis and format the errors.
        
        Args:
            paths: List of paths to analyze
            level: PHPStan rule level (0-9)
            config_path: Path to PHPStan config file
            verbose: Whether to run in verbose mode
            
        Returns:
            Tuple of (raw_output, return_code, formatted_batches)
        """
        # Run PHPStan analysis
        output, return_code = self.phpstan_runner.run_analysis(paths, level, config_path, verbose)
        
        # If analysis failed or no errors found, return early
        if return_code == 0:
            return output, return_code, []
        
        # Parse the errors
        errors = self.error_formatter.parse_phpstan_output(output)
        
        # Calculate total batches
        total_batches = self.error_formatter.get_total_batches(len(errors))
        
        # Format errors into batches
        batches = []
        for batch_idx in range(total_batches):
            formatted = self.error_formatter.format_for_mcp(errors, batch_idx)
            batches.append(formatted)
        
        return output, return_code, batches

    def prepare_mcp_message(self, 
                           batch: Dict[str, Any], 
                           file_contents: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Prepare a message for Claude Code via MCP.
        
        Args:
            batch: Formatted batch of errors
            file_contents: Dictionary mapping file paths to their contents
            
        Returns:
            MCP message dictionary
        """
        # If file_contents not provided, read the files
        if file_contents is None:
            file_contents = {}
            for file_path in batch["errors_by_file"].keys():
                full_path = os.path.join(self.project_path, file_path)
                if os.path.isfile(full_path):
                    with open(full_path, 'r') as f:
                        file_contents[file_path] = f.read()
        
        # Prepare the MCP message
        message = {
            "type": "mcp_phpstan_errors",
            "batch_info": batch["batch"],
            "errors": batch["errors_by_file"],
            "file_contents": file_contents,
            "project_path": self.project_path
        }
        
        return message

    def send_to_claude(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a message to Claude Code via MCP.
        
        This is a placeholder method that would be implemented with actual
        Claude API integration. For now, it just prints the message and
        returns a mock response.
        
        Args:
            message: MCP message to send
            
        Returns:
            Claude's response
        """
        print("Sending message to Claude Code via MCP:")
        print(json.dumps(message, indent=2))
        
        # This is where the actual API call to Claude would happen
        # For now, return a mock response
        return {
            "status": "success",
            "message": "This is a mock response. In a real implementation, this would be Claude's response.",
            "fixes": []
        }

    def apply_fixes(self, fixes: List[Dict[str, Any]]) -> bool:
        """
        Apply fixes suggested by Claude.
        
        This is a placeholder method that would be implemented to apply
        the fixes suggested by Claude to the PHP files.
        
        Args:
            fixes: List of fixes to apply
            
        Returns:
            True if all fixes were applied successfully, False otherwise
        """
        print("Applying fixes suggested by Claude:")
        print(json.dumps(fixes, indent=2))
        
        # This is where the actual fix application would happen
        # For now, just return success
        return True

    def process_phpstan_errors(self, 
                              paths: Optional[List[str]] = None,
                              level: Optional[int] = None,
                              config_path: Optional[str] = None,
                              verbose: bool = False,
                              max_iterations: int = 10) -> bool:
        """
        Process PHPStan errors with Claude Code via MCP.
        
        This method runs PHPStan, sends the errors to Claude, applies the fixes,
        and repeats until all errors are fixed or max_iterations is reached.
        
        Args:
            paths: List of paths to analyze
            level: PHPStan rule level (0-9)
            config_path: Path to PHPStan config file
            verbose: Whether to run in verbose mode
            max_iterations: Maximum number of iterations to run
            
        Returns:
            True if all errors were fixed, False otherwise
        """
        iteration = 0
        
        while iteration < max_iterations:
            print(f"\nIteration {iteration + 1}/{max_iterations}")
            
            # Run PHPStan analysis
            output, return_code, batches = self.run_phpstan_analysis(paths, level, config_path, verbose)
            
            # If no errors, we're done
            if return_code == 0:
                print("No PHPStan errors found. All fixed!")
                return True
            
            # If there are errors, process them in batches
            print(f"Found {len(batches)} batches of errors")
            
            for batch_idx, batch in enumerate(batches):
                print(f"\nProcessing batch {batch_idx + 1}/{len(batches)}")
                
                # Prepare MCP message
                message = self.prepare_mcp_message(batch)
                
                # Send to Claude
                response = self.send_to_claude(message)
                
                # Apply fixes
                if "fixes" in response and response["fixes"]:
                    success = self.apply_fixes(response["fixes"])
                    if not success:
                        print("Failed to apply fixes")
                        return False
                else:
                    print("No fixes suggested by Claude")
            
            # Increment iteration counter
            iteration += 1
        
        # If we've reached max_iterations, we've failed to fix all errors
        print(f"Reached maximum iterations ({max_iterations}) without fixing all errors")
        return False


def main():
    """Main entry point for the MCP client."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process PHPStan errors with Claude Code via MCP")
    parser.add_argument("project_path", help="Path to the PHP project")
    parser.add_argument("--paths", "-p", nargs="+", help="Paths to analyze")
    parser.add_argument("--level", "-l", type=int, help="PHPStan rule level (0-9)")
    parser.add_argument("--config", "-c", help="Path to PHPStan config file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Run in verbose mode")
    parser.add_argument("--max-errors", "-m", type=int, default=3, help="Maximum errors per batch")
    parser.add_argument("--max-iterations", "-i", type=int, default=10, help="Maximum iterations")
    
    args = parser.parse_args()
    
    # Initialize MCP client
    client = McpClient(args.project_path, args.max_errors)
    
    # Process PHPStan errors
    success = client.process_phpstan_errors(
        args.paths,
        args.level,
        args.config,
        args.verbose,
        args.max_iterations
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
