"""
Claude Code MCP Integration for PHPStan

This module provides the integration between Claude Code and PHPStan via MCP.
It allows Claude Code to run PHPStan analysis and fix errors interactively.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional, Tuple

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.McpIntegration.McpClient import McpClient


class ClaudeCodeMcpHandler:
    """Handler for Claude Code MCP commands related to PHPStan."""

    def __init__(self, project_path: str, max_errors_per_batch: int = 3):
        """
        Initialize the Claude Code MCP handler.
        
        Args:
            project_path: Path to the PHP project
            max_errors_per_batch: Maximum number of errors to process in a single batch
        """
        self.project_path = os.path.abspath(project_path)
        self.max_errors_per_batch = max_errors_per_batch
        
        # Initialize MCP client
        self.mcp_client = McpClient(self.project_path, self.max_errors_per_batch)
        
        # Initialize state
        self.current_batches = []
        self.current_batch_idx = 0
        self.total_errors = 0
        self.fixed_errors = 0

    def handle_command(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a Claude Code MCP command.
        
        Args:
            command: Command to handle
            args: Command arguments
            
        Returns:
            Response to the command
        """
        if command == "run_phpstan":
            return self.handle_run_phpstan(args)
        elif command == "fix_errors":
            return self.handle_fix_errors(args)
        elif command == "list_errors":
            return self.handle_list_errors(args)
        elif command == "select_errors":
            return self.handle_select_errors(args)
        else:
            return {
                "status": "error",
                "message": f"Unknown command: {command}"
            }

    def handle_run_phpstan(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the run_phpstan command.
        
        Args:
            args: Command arguments
            
        Returns:
            Response to the command
        """
        paths = args.get("paths")
        level = args.get("level")
        config_path = args.get("config_path")
        verbose = args.get("verbose", False)
        
        # Run PHPStan analysis
        output, return_code, batches = self.mcp_client.run_phpstan_analysis(
            paths, level, config_path, verbose
        )
        
        # Store the batches
        self.current_batches = batches
        self.current_batch_idx = 0
        
        # Calculate total errors
        self.total_errors = sum(len(batch['errors_by_file'][file]) for batch in batches for file in batch['errors_by_file'])
        
        # Prepare response
        if return_code == 0:
            return {
                "status": "success",
                "message": "No PHPStan errors found!",
                "errors": 0,
                "batches": 0
            }
        else:
            # If there are too many errors, only show the first 10
            if self.total_errors > 10:
                first_10_errors = self.get_first_n_errors(10)
                return {
                    "status": "success",
                    "message": f"Found {self.total_errors} errors in {len(batches)} batches. Showing first 10 errors:",
                    "errors": self.total_errors,
                    "batches": len(batches),
                    "first_10_errors": first_10_errors,
                    "too_many_errors": True
                }
            else:
                all_errors = self.get_first_n_errors(self.total_errors)
                return {
                    "status": "success",
                    "message": f"Found {self.total_errors} errors in {len(batches)} batches:",
                    "errors": self.total_errors,
                    "batches": len(batches),
                    "all_errors": all_errors,
                    "too_many_errors": False
                }

    def handle_fix_errors(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the fix_errors command.
        
        Args:
            args: Command arguments
            
        Returns:
            Response to the command
        """
        batch_idx = args.get("batch_index", self.current_batch_idx)
        error_indices = args.get("error_indices")
        
        # Check if there are batches
        if not self.current_batches:
            return {
                "status": "error",
                "message": "No PHPStan errors to fix. Run PHPStan analysis first."
            }
        
        # Check if batch index is valid
        if batch_idx < 0 or batch_idx >= len(self.current_batches):
            return {
                "status": "error",
                "message": f"Invalid batch index: {batch_idx}. Valid range: 0-{len(self.current_batches) - 1}"
            }
        
        # Get the batch
        batch = self.current_batches[batch_idx]
        
        # If error_indices is provided, filter the batch to only include those errors
        if error_indices is not None:
            filtered_batch = self.filter_batch_by_indices(batch, error_indices)
            if not filtered_batch:
                return {
                    "status": "error",
                    "message": f"No valid error indices found in {error_indices}"
                }
            batch = filtered_batch
        
        # Prepare MCP message
        message = self.mcp_client.prepare_mcp_message(batch)
        
        # Send to Claude
        response = self.mcp_client.send_to_claude(message)
        
        # Apply fixes
        if "fixes" in response and response["fixes"]:
            success = self.mcp_client.apply_fixes(response["fixes"])
            
            if success:
                # Update fixed errors count
                self.fixed_errors += len(response["fixes"])
                
                # Run PHPStan again to get updated errors
                output, return_code, batches = self.mcp_client.run_phpstan_analysis()
                
                # Update batches
                self.current_batches = batches
                self.current_batch_idx = min(batch_idx, len(batches) - 1) if batches else 0
                
                # Calculate remaining errors
                remaining_errors = sum(len(batch['errors_by_file'][file]) for batch in batches for file in batch['errors_by_file'])
                
                return {
                    "status": "success",
                    "message": f"Applied {len(response['fixes'])} fixes successfully!",
                    "fixes": response["fixes"],
                    "remaining_errors": remaining_errors,
                    "fixed_errors": self.fixed_errors,
                    "all_fixed": return_code == 0
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to apply fixes.",
                    "fixes": response["fixes"]
                }
        else:
            return {
                "status": "warning",
                "message": "No fixes suggested by Claude.",
                "raw_response": response.get("raw_response", "")
            }

    def handle_list_errors(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the list_errors command.
        
        Args:
            args: Command arguments
            
        Returns:
            Response to the command
        """
        batch_idx = args.get("batch_index", self.current_batch_idx)
        max_errors = args.get("max_errors", 10)
        
        # Check if there are batches
        if not self.current_batches:
            return {
                "status": "error",
                "message": "No PHPStan errors to list. Run PHPStan analysis first."
            }
        
        # Check if batch index is valid
        if batch_idx < 0 or batch_idx >= len(self.current_batches):
            return {
                "status": "error",
                "message": f"Invalid batch index: {batch_idx}. Valid range: 0-{len(self.current_batches) - 1}"
            }
        
        # Get the errors
        errors = self.get_first_n_errors(max_errors, batch_idx)
        
        return {
            "status": "success",
            "message": f"Listing errors for batch {batch_idx + 1}/{len(self.current_batches)}:",
            "errors": errors,
            "batch_index": batch_idx,
            "total_batches": len(self.current_batches)
        }

    def handle_select_errors(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the select_errors command.
        
        Args:
            args: Command arguments
            
        Returns:
            Response to the command
        """
        error_indices = args.get("error_indices", [])
        batch_idx = args.get("batch_index", self.current_batch_idx)
        
        # Check if there are batches
        if not self.current_batches:
            return {
                "status": "error",
                "message": "No PHPStan errors to select. Run PHPStan analysis first."
            }
        
        # Check if batch index is valid
        if batch_idx < 0 or batch_idx >= len(self.current_batches):
            return {
                "status": "error",
                "message": f"Invalid batch index: {batch_idx}. Valid range: 0-{len(self.current_batches) - 1}"
            }
        
        # Get the batch
        batch = self.current_batches[batch_idx]
        
        # Filter the batch to only include the selected errors
        filtered_batch = self.filter_batch_by_indices(batch, error_indices)
        
        if not filtered_batch:
            return {
                "status": "error",
                "message": f"No valid error indices found in {error_indices}"
            }
        
        # Store the filtered batch
        self.current_batches[batch_idx] = filtered_batch
        
        # Get the selected errors
        selected_errors = self.get_errors_from_batch(filtered_batch)
        
        return {
            "status": "success",
            "message": f"Selected {len(selected_errors)} errors for fixing:",
            "selected_errors": selected_errors,
            "batch_index": batch_idx
        }

    def get_first_n_errors(self, n: int, batch_idx: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get the first N errors from all batches or a specific batch.
        
        Args:
            n: Maximum number of errors to return
            batch_idx: Index of the batch to get errors from, or None for all batches
            
        Returns:
            List of errors
        """
        errors = []
        
        if batch_idx is not None:
            # Get errors from a specific batch
            if 0 <= batch_idx < len(self.current_batches):
                batch = self.current_batches[batch_idx]
                errors = self.get_errors_from_batch(batch)
        else:
            # Get errors from all batches
            for batch in self.current_batches:
                batch_errors = self.get_errors_from_batch(batch)
                errors.extend(batch_errors)
                if len(errors) >= n:
                    break
        
        # Limit to the first N errors
        return errors[:n]

    def get_errors_from_batch(self, batch: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get all errors from a batch.
        
        Args:
            batch: Batch to get errors from
            
        Returns:
            List of errors
        """
        errors = []
        
        for file_path, file_errors in batch["errors_by_file"].items():
            for error in file_errors:
                errors.append({
                    "file": file_path,
                    "line": error.get("line", "?"),
                    "message": error.get("message", "Unknown error"),
                    "index": len(errors)
                })
        
        return errors

    def filter_batch_by_indices(self, batch: Dict[str, Any], indices: List[int]) -> Dict[str, Any]:
        """
        Filter a batch to only include errors with the given indices.
        
        Args:
            batch: Batch to filter
            indices: Indices of errors to include
            
        Returns:
            Filtered batch
        """
        # Get all errors from the batch
        all_errors = self.get_errors_from_batch(batch)
        
        # Filter errors by index
        filtered_errors = [error for error in all_errors if error["index"] in indices]
        
        # Create a new batch with only the filtered errors
        filtered_batch = {
            "batch": batch["batch"],
            "errors_by_file": {}
        }
        
        # Group filtered errors by file
        for error in filtered_errors:
            file_path = error["file"]
            if file_path not in filtered_batch["errors_by_file"]:
                filtered_batch["errors_by_file"][file_path] = []
            
            # Find the original error in the batch
            for original_error in batch["errors_by_file"][file_path]:
                if original_error.get("line") == error["line"] and original_error.get("message") == error["message"]:
                    filtered_batch["errors_by_file"][file_path].append(original_error)
                    break
        
        return filtered_batch


def main():
    """Main entry point for the Claude Code MCP handler."""
    parser = argparse.ArgumentParser(description="Claude Code MCP handler for PHPStan")
    parser.add_argument("project_path", help="Path to the PHP project")
    parser.add_argument("--command", "-c", required=True, help="Command to handle")
    parser.add_argument("--args", "-a", help="JSON-encoded command arguments")
    parser.add_argument("--max-errors", "-m", type=int, default=3, help="Maximum errors per batch")
    
    args = parser.parse_args()
    
    # Parse command arguments
    command_args = {}
    if args.args:
        try:
            command_args = json.loads(args.args)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in command arguments: {args.args}")
            sys.exit(1)
    
    # Initialize handler
    handler = ClaudeCodeMcpHandler(args.project_path, args.max_errors)
    
    # Handle command
    response = handler.handle_command(args.command, command_args)
    
    # Print response as JSON
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    main()
