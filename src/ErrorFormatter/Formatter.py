"""
PHPStan Error Formatter for MCP

This module formats PHPStan errors into a structure suitable for processing by Claude via MCP.
It handles parsing the PHPStan output and converting it to a format that can be used with MCP.
"""

import json
import re
from typing import Dict, List, Optional, Any


class PhpStanError:
    """Represents a single PHPStan error."""

    def __init__(
        self,
        message: str,
        file: str,
        line: int,
        error_type: str,
        error_code: Optional[str] = None,
        suggestion: Optional[str] = None,
    ):
        self.message = message
        self.file = file
        self.line = line
        self.error_type = error_type
        self.error_code = error_code
        self.suggestion = suggestion

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary representation."""
        result = {
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "error_type": self.error_type,
        }
        
        if self.error_code:
            result["error_code"] = self.error_code
            
        if self.suggestion:
            result["suggestion"] = self.suggestion
            
        return result


class PhpStanErrorFormatter:
    """Formats PHPStan errors for MCP integration."""

    def __init__(self, max_errors_per_batch: int = 5):
        """
        Initialize the formatter.
        
        Args:
            max_errors_per_batch: Maximum number of errors to include in a single batch
        """
        self.max_errors_per_batch = max_errors_per_batch

    def parse_phpstan_output(self, output: str) -> List[PhpStanError]:
        """
        Parse PHPStan CLI output and extract errors.
        
        Args:
            output: The raw output from PHPStan
            
        Returns:
            List of PhpStanError objects
        """
        errors = []
        
        # Find file sections in the output
        file_sections = re.findall(
            r'------ +-+ +\n +Line +([^\n]+) +\n +------ +-+ +\n(.*?)(?=\n +------ +-|$)',
            output,
            re.DOTALL
        )
        
        for file_name, section_content in file_sections:
            # Extract individual errors from each file section
            error_matches = re.finditer(
                r' +(\d+) +([^\n]+)\n +🪪 +([^\n]+)(?:\n +💡 +([^\n]+))?',
                section_content
            )
            
            for match in error_matches:
                line_num = int(match.group(1))
                message = match.group(2).strip()
                error_code = match.group(3).strip()
                suggestion = match.group(4).strip() if match.group(4) else None
                
                # Determine error type from the message or code
                error_type = self._determine_error_type(message, error_code)
                
                errors.append(PhpStanError(
                    message=message,
                    file=file_name.strip(),
                    line=line_num,
                    error_type=error_type,
                    error_code=error_code,
                    suggestion=suggestion
                ))
        
        return errors

    def _determine_error_type(self, message: str, error_code: str) -> str:
        """
        Determine the type of error based on the message and error code.
        
        Args:
            message: Error message
            error_code: Error code from PHPStan
            
        Returns:
            Error type classification
        """
        if "undefined" in error_code.lower():
            return "undefined_symbol"
        elif "type" in error_code.lower():
            return "type_error"
        elif "missing" in error_code.lower():
            return "missing_type"
        elif "not.found" in error_code.lower():
            return "not_found"
        elif "arguments" in error_code.lower():
            return "argument_error"
        else:
            return "other"

    def format_for_mcp(self, errors: List[PhpStanError], batch_index: int = 0) -> Dict[str, Any]:
        """
        Format errors for MCP integration.
        
        Args:
            errors: List of PHPStan errors
            batch_index: Index of the current batch when processing incrementally
            
        Returns:
            Dictionary formatted for MCP
        """
        # Calculate the slice of errors for this batch
        start_idx = batch_index * self.max_errors_per_batch
        end_idx = start_idx + self.max_errors_per_batch
        batch_errors = errors[start_idx:end_idx]
        
        # Group errors by file
        errors_by_file = {}
        for error in batch_errors:
            if error.file not in errors_by_file:
                errors_by_file[error.file] = []
            errors_by_file[error.file].append(error.to_dict())
        
        # Format for MCP
        return {
            "batch": {
                "index": batch_index,
                "total_errors": len(errors),
                "batch_size": len(batch_errors),
                "has_more": end_idx < len(errors)
            },
            "errors_by_file": errors_by_file
        }

    def get_total_batches(self, total_errors: int) -> int:
        """
        Calculate the total number of batches needed.
        
        Args:
            total_errors: Total number of errors
            
        Returns:
            Number of batches needed
        """
        return (total_errors + self.max_errors_per_batch - 1) // self.max_errors_per_batch


def format_phpstan_output(phpstan_output: str, max_errors_per_batch: int = 5, batch_index: int = 0) -> str:
    """
    Format PHPStan output for MCP.
    
    Args:
        phpstan_output: Raw PHPStan output
        max_errors_per_batch: Maximum errors per batch
        batch_index: Current batch index
        
    Returns:
        JSON string formatted for MCP
    """
    formatter = PhpStanErrorFormatter(max_errors_per_batch)
    errors = formatter.parse_phpstan_output(phpstan_output)
    formatted = formatter.format_for_mcp(errors, batch_index)
    return json.dumps(formatted, indent=2)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        # Read PHPStan output from file
        with open(sys.argv[1], 'r') as f:
            phpstan_output = f.read()
    else:
        # Read from stdin
        phpstan_output = sys.stdin.read()
    
    # Parse batch index if provided
    batch_index = 0
    if len(sys.argv) > 2:
        try:
            batch_index = int(sys.argv[2])
        except ValueError:
            pass
    
    # Parse max errors per batch if provided
    max_errors = 5
    if len(sys.argv) > 3:
        try:
            max_errors = int(sys.argv[3])
        except ValueError:
            pass
    
    # Format and print
    formatted_output = format_phpstan_output(phpstan_output, max_errors, batch_index)
    print(formatted_output)
