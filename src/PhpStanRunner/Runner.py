"""
PHPStan Runner Module

This module provides functionality to run PHPStan on PHP projects and capture the output.
"""

import subprocess
import os
import sys
from typing import Dict, List, Optional, Tuple, Any


class PhpStanRunner:
    """Runs PHPStan and captures the output."""

    def __init__(self, project_path: str, phpstan_binary: Optional[str] = None):
        """
        Initialize the PHPStan runner.
        
        Args:
            project_path: Path to the PHP project
            phpstan_binary: Path to the PHPStan binary (defaults to vendor/bin/phpstan)
        """
        self.project_path = os.path.abspath(project_path)
        
        if phpstan_binary:
            self.phpstan_binary = phpstan_binary
        else:
            # Default PHPStan binary path
            self.phpstan_binary = os.path.join(self.project_path, "vendor/bin/phpstan")
        
        # Check if the project path exists
        if not os.path.isdir(self.project_path):
            raise ValueError(f"Project path does not exist: {self.project_path}")

    def run_analysis(self, 
                    paths: Optional[List[str]] = None, 
                    level: Optional[int] = None,
                    config_path: Optional[str] = None,
                    verbose: bool = False) -> Tuple[str, int]:
        """
        Run PHPStan analysis on the project.
        
        Args:
            paths: List of paths to analyze (defaults to paths in config)
            level: PHPStan rule level (0-9, defaults to level in config)
            config_path: Path to PHPStan config file (defaults to phpstan.neon in project root)
            verbose: Whether to run in verbose mode
            
        Returns:
            Tuple of (output, return_code)
        """
        # Build the command
        cmd = [self.phpstan_binary, "analyse"]
        
        # Add verbose flag if requested
        if verbose:
            cmd.append("-v")
        
        # Add level if specified
        if level is not None:
            cmd.extend(["--level", str(level)])
        
        # Add config path if specified
        if config_path:
            cmd.extend(["--configuration", config_path])
        
        # Add paths to analyze if specified
        if paths:
            cmd.extend(paths)
        
        # Run the command
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout + result.stderr, result.returncode
        except subprocess.SubprocessError as e:
            return f"Error running PHPStan: {str(e)}", 1
        except Exception as e:
            return f"Unexpected error: {str(e)}", 1

    def check_installation(self) -> bool:
        """
        Check if PHPStan is properly installed.
        
        Returns:
            True if PHPStan is installed, False otherwise
        """
        if not os.path.isfile(self.phpstan_binary):
            return False
            
        try:
            result = subprocess.run(
                [self.phpstan_binary, "--version"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except Exception:
            return False


def run_phpstan(project_path: str, 
               output_file: Optional[str] = None,
               paths: Optional[List[str]] = None,
               level: Optional[int] = None,
               config_path: Optional[str] = None,
               verbose: bool = False) -> Tuple[str, int]:
    """
    Run PHPStan on a project and optionally save the output to a file.
    
    Args:
        project_path: Path to the PHP project
        output_file: Path to save the output (if None, output is just returned)
        paths: List of paths to analyze
        level: PHPStan rule level (0-9)
        config_path: Path to PHPStan config file
        verbose: Whether to run in verbose mode
        
    Returns:
        Tuple of (output, return_code)
    """
    runner = PhpStanRunner(project_path)
    
    # Check if PHPStan is installed
    if not runner.check_installation():
        error_msg = (
            "PHPStan is not installed or not found at the expected location. "
            "Please run 'composer require --dev phpstan/phpstan' in your project."
        )
        if output_file:
            with open(output_file, 'w') as f:
                f.write(error_msg)
        return error_msg, 1
    
    # Run the analysis
    output, return_code = runner.run_analysis(paths, level, config_path, verbose)
    
    # Save to file if requested
    if output_file:
        with open(output_file, 'w') as f:
            f.write(output)
    
    return output, return_code


if __name__ == "__main__":
    # Simple CLI interface
    import argparse
    
    parser = argparse.ArgumentParser(description="Run PHPStan analysis")
    parser.add_argument("project_path", help="Path to the PHP project")
    parser.add_argument("--output", "-o", help="Path to save the output")
    parser.add_argument("--paths", "-p", nargs="+", help="Paths to analyze")
    parser.add_argument("--level", "-l", type=int, help="PHPStan rule level (0-9)")
    parser.add_argument("--config", "-c", help="Path to PHPStan config file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Run in verbose mode")
    
    args = parser.parse_args()
    
    output, return_code = run_phpstan(
        args.project_path,
        args.output,
        args.paths,
        args.level,
        args.config,
        args.verbose
    )
    
    if not args.output:
        print(output)
    
    sys.exit(return_code)
