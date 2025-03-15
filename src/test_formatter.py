"""
Test script for PHPStan error formatter.
"""

import sys
import os
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ErrorFormatter.Formatter import format_phpstan_output
from src.PhpStanRunner.Runner import run_phpstan

def main():
    # Path to the sample PHP project
    project_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               'samples', 'php_project')
    
    # Run PHPStan analysis
    print("Running PHPStan analysis...")
    phpstan_output, return_code = run_phpstan(project_path, verbose=True)
    
    if return_code != 0:
        print(f"PHPStan analysis completed with {return_code} errors.")
    else:
        print("PHPStan analysis completed successfully (no errors).")
    
    # Format the output for different batch sizes
    print("\nFormatting errors (batch size: 3, batch index: 0):")
    formatted_output = format_phpstan_output(phpstan_output, max_errors_per_batch=3, batch_index=0)
    print(formatted_output)
    
    # Parse the formatted output to check batch information
    parsed = json.loads(formatted_output)
    total_errors = parsed["batch"]["total_errors"]
    
    if parsed["batch"]["has_more"]:
        print("\nFormatting errors (batch size: 3, batch index: 1):")
        formatted_output = format_phpstan_output(phpstan_output, max_errors_per_batch=3, batch_index=1)
        print(formatted_output)

if __name__ == "__main__":
    main()
