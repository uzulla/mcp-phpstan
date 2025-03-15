"""
Test script for MCP integration with PHPStan.
"""

import sys
import os
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.McpIntegration.McpClient import McpClient


def main():
    """Test the MCP integration with PHPStan."""
    # Path to the sample PHP project
    project_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               'samples', 'php_project')
    
    # Initialize MCP client
    client = McpClient(project_path, max_errors_per_batch=3)
    
    # Run PHPStan analysis and get formatted batches
    print("Running PHPStan analysis...")
    output, return_code, batches = client.run_phpstan_analysis(verbose=True)
    
    if return_code != 0:
        print(f"PHPStan analysis completed with errors. Found {len(batches)} batches.")
    else:
        print("PHPStan analysis completed successfully (no errors).")
        return
    
    # Process the first batch
    if batches:
        print("\nPreparing MCP message for first batch:")
        message = client.prepare_mcp_message(batches[0])
        
        # Print the message (in a real scenario, this would be sent to Claude)
        print(json.dumps(message, indent=2))
        
        # Simulate sending to Claude
        print("\nSimulating sending to Claude...")
        response = client.send_to_claude(message)
        
        print("\nMock response from Claude:")
        print(json.dumps(response, indent=2))
    else:
        print("No error batches found.")


if __name__ == "__main__":
    main()
