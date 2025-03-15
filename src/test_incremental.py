"""
Test script for incremental PHPStan error processing.
"""

import sys
import os
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.incremental_processor import IncrementalProcessor


def main():
    """Test the incremental processor."""
    # Path to the sample PHP project
    project_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               'samples', 'php_project')
    
    # Create a test processor
    processor = IncrementalProcessor(
        project_path,
        max_errors_per_batch=2,
        max_iterations=2,
        verbose=True
    )
    
    # Run a test process (dry run)
    print('Testing incremental processor...')
    processor.process()
    
    # Print stats
    print('\nProcessor stats:')
    print(json.dumps(processor.get_stats(), indent=2))


if __name__ == "__main__":
    main()
