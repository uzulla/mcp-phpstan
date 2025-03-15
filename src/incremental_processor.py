"""
Incremental PHPStan Error Processor

This module provides functionality to incrementally process PHPStan errors
with Claude Code via MCP, processing a few errors at a time until all are fixed.
"""

import os
import sys
import time
import json
from typing import Dict, List, Optional, Any, Tuple

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.PhpStanRunner.Runner import PhpStanRunner
from src.ErrorFormatter.Formatter import PhpStanErrorFormatter
from src.McpIntegration.McpClient import McpClient


class IncrementalProcessor:
    """Processes PHPStan errors incrementally with Claude Code via MCP."""

    def __init__(self, 
                 project_path: str,
                 max_errors_per_batch: int = 3,
                 max_iterations: int = 10,
                 phpstan_binary: Optional[str] = None,
                 verbose: bool = False):
        """
        Initialize the incremental processor.
        
        Args:
            project_path: Path to the PHP project
            max_errors_per_batch: Maximum number of errors to process in a single batch
            max_iterations: Maximum number of iterations to run
            phpstan_binary: Path to the PHPStan binary
            verbose: Whether to run in verbose mode
        """
        self.project_path = os.path.abspath(project_path)
        self.max_errors_per_batch = max_errors_per_batch
        self.max_iterations = max_iterations
        self.verbose = verbose
        
        # Initialize MCP client
        self.mcp_client = McpClient(project_path, max_errors_per_batch, phpstan_binary)
        
        # Initialize PHPStan runner
        self.phpstan_runner = PhpStanRunner(project_path, phpstan_binary)
        
        # Initialize error formatter
        self.error_formatter = PhpStanErrorFormatter(max_errors_per_batch)
        
        # Statistics
        self.stats = {
            "iterations": 0,
            "total_errors_fixed": 0,
            "total_batches_processed": 0,
            "errors_by_type": {}
        }

    def process(self, 
               paths: Optional[List[str]] = None,
               level: Optional[int] = None,
               config_path: Optional[str] = None) -> bool:
        """
        Process PHPStan errors incrementally.
        
        Args:
            paths: List of paths to analyze
            level: PHPStan rule level (0-9)
            config_path: Path to PHPStan config file
            
        Returns:
            True if all errors were fixed, False otherwise
        """
        iteration = 0
        total_errors_fixed = 0
        
        while iteration < self.max_iterations:
            print(f"\n=== Iteration {iteration + 1}/{self.max_iterations} ===")
            
            # Run PHPStan analysis
            output, return_code, batches = self.mcp_client.run_phpstan_analysis(
                paths, level, config_path, self.verbose
            )
            
            # If no errors, we're done
            if return_code == 0:
                print(f"\n✅ All PHPStan errors fixed! Total fixed: {total_errors_fixed}")
                self.stats["iterations"] = iteration + 1
                self.stats["total_errors_fixed"] = total_errors_fixed
                return True
            
            # Get total errors in this iteration
            total_errors = sum(batch["batch"]["batch_size"] for batch in batches)
            print(f"Found {total_errors} errors in {len(batches)} batches")
            
            # Process batches one by one
            errors_fixed_this_iteration = 0
            
            for batch_idx, batch in enumerate(batches):
                print(f"\n--- Processing batch {batch_idx + 1}/{len(batches)} ---")
                batch_size = batch["batch"]["batch_size"]
                
                # Prepare MCP message with file contents
                file_contents = self._get_file_contents(batch["errors_by_file"].keys())
                message = self.mcp_client.prepare_mcp_message(batch, file_contents)
                
                # Send to Claude
                print(f"Sending batch with {batch_size} errors to Claude...")
                response = self.mcp_client.send_to_claude(message)
                
                # Apply fixes
                if "fixes" in response and response["fixes"]:
                    num_fixes = len(response["fixes"])
                    print(f"Applying {num_fixes} fixes suggested by Claude...")
                    
                    success = self.mcp_client.apply_fixes(response["fixes"])
                    if success:
                        errors_fixed_this_iteration += num_fixes
                        self._update_error_stats(batch)
                    else:
                        print("❌ Failed to apply fixes")
                        return False
                else:
                    print("⚠️ No fixes suggested by Claude for this batch")
                
                # Update statistics
                self.stats["total_batches_processed"] += 1
                
                # Optional: Add a delay between batches to avoid rate limiting
                if batch_idx < len(batches) - 1:
                    time.sleep(1)
            
            # Update total errors fixed
            total_errors_fixed += errors_fixed_this_iteration
            
            # If no errors were fixed in this iteration, we're stuck
            if errors_fixed_this_iteration == 0:
                print(f"\n⚠️ No errors fixed in iteration {iteration + 1}. Stopping.")
                self.stats["iterations"] = iteration + 1
                self.stats["total_errors_fixed"] = total_errors_fixed
                return False
            
            print(f"\nFixed {errors_fixed_this_iteration} errors in iteration {iteration + 1}")
            print(f"Total errors fixed so far: {total_errors_fixed}")
            
            # Increment iteration counter
            iteration += 1
        
        # If we've reached max_iterations, we've failed to fix all errors
        print(f"\n⚠️ Reached maximum iterations ({self.max_iterations}) without fixing all errors")
        print(f"Total errors fixed: {total_errors_fixed}")
        
        self.stats["iterations"] = self.max_iterations
        self.stats["total_errors_fixed"] = total_errors_fixed
        
        return False

    def _get_file_contents(self, file_paths: List[str]) -> Dict[str, str]:
        """
        Get the contents of the specified files.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            Dictionary mapping file paths to their contents
        """
        file_contents = {}
        
        for file_path in file_paths:
            full_path = os.path.join(self.project_path, file_path)
            if os.path.isfile(full_path):
                try:
                    with open(full_path, 'r') as f:
                        file_contents[file_path] = f.read()
                except Exception as e:
                    print(f"Error reading file {file_path}: {str(e)}")
        
        return file_contents

    def _update_error_stats(self, batch: Dict[str, Any]) -> None:
        """
        Update error statistics.
        
        Args:
            batch: Batch of errors
        """
        for file_path, errors in batch["errors_by_file"].items():
            for error in errors:
                error_type = error.get("error_type", "other")
                
                if error_type not in self.stats["errors_by_type"]:
                    self.stats["errors_by_type"][error_type] = 0
                
                self.stats["errors_by_type"][error_type] += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the processing.
        
        Returns:
            Dictionary of statistics
        """
        return self.stats


def main() -> int:
    """Main entry point for the incremental processor."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Incrementally process PHPStan errors with Claude Code via MCP"
    )
    
    # Required arguments
    parser.add_argument(
        "project_path",
        help="Path to the PHP project to analyze"
    )
    
    # PHPStan options
    parser.add_argument(
        "--paths", "-p",
        nargs="+",
        help="Paths to analyze (defaults to paths in phpstan.neon)"
    )
    parser.add_argument(
        "--level", "-l",
        type=int,
        help="PHPStan rule level (0-9, defaults to level in phpstan.neon)"
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to PHPStan config file (defaults to phpstan.neon in project root)"
    )
    
    # Processing options
    parser.add_argument(
        "--max-errors", "-m",
        type=int,
        default=3,
        help="Maximum errors per batch (default: 3)"
    )
    parser.add_argument(
        "--max-iterations", "-i",
        type=int,
        default=10,
        help="Maximum iterations to run (default: 10)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Run in verbose mode"
    )
    parser.add_argument(
        "--stats-file",
        help="Path to save statistics to"
    )
    
    args = parser.parse_args()
    
    # Initialize incremental processor
    processor = IncrementalProcessor(
        args.project_path,
        args.max_errors,
        args.max_iterations,
        verbose=args.verbose
    )
    
    # Process PHPStan errors
    success = processor.process(args.paths, args.level, args.config)
    
    # Save statistics if requested
    if args.stats_file:
        stats = processor.get_stats()
        with open(args.stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
