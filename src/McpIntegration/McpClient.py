"""
MCP (Multi-agent Conversation Protocol) Client for PHPStan Integration

This module provides functionality to integrate PHPStan with Claude Code via MCP.
It handles sending PHPStan errors to Claude and processing the responses.
"""

import json
import os
import sys
import time
import dotenv
from typing import Dict, List, Optional, Any, Tuple

# Load environment variables from .env file if it exists
dotenv.load_dotenv()

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
        
        Uses the Anthropic Claude API to send PHPStan errors and receive fixes.
        
        Args:
            message: MCP message to send
            
        Returns:
            Claude's response with fixes
        """
        try:
            import requests
            
            # Get API key from environment variable
            api_key = os.environ.get("CLAUDE_API_KEY")
            if not api_key:
                return {
                    "status": "error",
                    "message": "CLAUDE_API_KEY environment variable not set. Please set it in .env file or as an environment variable.",
                    "fixes": []
                }
            
            # Prepare the request headers
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }
            
            # Prepare the system prompt
            system_prompt = """
            You are a PHP expert who specializes in fixing code issues detected by PHPStan.
            You will receive PHPStan errors along with the PHP code that contains these errors.
            Your task is to analyze each error and suggest a fix.
            
            For each error:
            1. Understand the error message and locate the issue in the code
            2. Determine the appropriate fix
            3. Return the fix in a structured format
            
            Your response should be in JSON format with the following structure:
            {
                "fixes": [
                    {
                        "file": "path/to/file.php",
                        "line": 123,
                        "original_code": "the original problematic code",
                        "fixed_code": "the fixed code",
                        "explanation": "explanation of what was wrong and how it was fixed"
                    },
                    ...
                ]
            }
            """
            
            # Format the user message
            user_message = f"""
            I need help fixing PHPStan errors in my PHP code.
            
            Here are the errors:
            {json.dumps(message['errors'], indent=2)}
            
            Here are the file contents:
            """
            
            # Add file contents to the user message
            for file_path, content in message['file_contents'].items():
                user_message += f"\n\n--- {file_path} ---\n{content}"
            
            # Prepare the request body
            request_body = {
                "model": "claude-3-opus-20240229",
                "max_tokens": 4000,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            }
            
            print("Sending request to Claude API...")
            
            # Send the request to Claude
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=request_body
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                claude_response = response.json()
                
                # Extract the content from Claude's response
                content = claude_response["content"][0]["text"]
                
                # Try to parse the JSON response
                try:
                    # Find JSON in the response
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        json_content = content[json_start:json_end]
                        fixes_data = json.loads(json_content)
                        
                        return {
                            "status": "success",
                            "message": "Successfully received fixes from Claude",
                            "fixes": fixes_data.get("fixes", [])
                        }
                    else:
                        # If no JSON found, try to extract fixes manually
                        return {
                            "status": "partial_success",
                            "message": "Received response from Claude but couldn't parse JSON. Using the full response.",
                            "fixes": [],
                            "raw_response": content
                        }
                except json.JSONDecodeError:
                    return {
                        "status": "partial_success",
                        "message": "Received response from Claude but couldn't parse JSON. Using the full response.",
                        "fixes": [],
                        "raw_response": content
                    }
            else:
                return {
                    "status": "error",
                    "message": f"Error communicating with Claude API: {response.status_code} - {response.text}",
                    "fixes": []
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Exception when communicating with Claude: {str(e)}",
                "fixes": []
            }

    def apply_fixes(self, fixes: List[Dict[str, Any]]) -> bool:
        """
        Apply fixes suggested by Claude to the PHP files.
        
        Args:
            fixes: List of fixes to apply, each containing file, line, original_code, and fixed_code
            
        Returns:
            True if all fixes were applied successfully, False otherwise
        """
        if not fixes:
            print("No fixes to apply")
            return True
        
        print(f"Applying {len(fixes)} fixes suggested by Claude:")
        
        success_count = 0
        
        for fix in fixes:
            try:
                # Extract fix information
                file_path = fix.get("file")
                original_code = fix.get("original_code")
                fixed_code = fix.get("fixed_code")
                explanation = fix.get("explanation", "No explanation provided")
                
                if not file_path or not original_code or not fixed_code:
                    print(f"⚠️ Skipping fix due to missing information: {json.dumps(fix)}")
                    continue
                
                # Get the full path to the file
                # Try multiple possible paths to find the file
                possible_paths = [
                    os.path.join(self.project_path, file_path),                    # Direct path
                    os.path.join(self.project_path, 'src', file_path),             # With src/ prefix
                    os.path.join(self.project_path, file_path.replace('src/', '')),# Remove src/ if present
                    os.path.join(self.project_path, 'src', file_path.replace('src/', '')) # Replace src/ with project's src/
                ]
                
                # Find the first path that exists
                full_path = None
                for path in possible_paths:
                    if os.path.isfile(path):
                        full_path = path
                        break
                
                # If no path exists, skip this fix
                if not full_path:
                    print(f"⚠️ File not found: {file_path}")
                    print(f"Tried paths: {possible_paths}")
                    continue
                
                # Read the file content
                with open(full_path, 'r') as f:
                    content = f.read()
                
                # Check if the original code is in the file
                if original_code not in content:
                    # Try to find a close match by normalizing whitespace
                    normalized_original = ' '.join(original_code.split())
                    normalized_content = ' '.join(content.split())
                    
                    if normalized_original in normalized_content:
                        # Find the actual code in the file that matches the normalized version
                        import re
                        pattern = re.escape(normalized_original).replace('\\ ', '\\s+')
                        matches = re.findall(pattern, normalized_content)
                        
                        if matches:
                            # Find the actual code in the original content
                            for line in content.split('\n'):
                                normalized_line = ' '.join(line.split())
                                if normalized_original in normalized_line:
                                    original_code = line
                                    break
                    else:
                        print(f"⚠️ Original code not found in {file_path}:")
                        print(f"Original: {original_code}")
                        continue
                
                # Replace the original code with the fixed code
                new_content = content.replace(original_code, fixed_code)
                
                # Write the new content back to the file
                with open(full_path, 'w') as f:
                    f.write(new_content)
                
                print(f"✅ Applied fix to {file_path}:")
                print(f"Explanation: {explanation}")
                print(f"Original: {original_code}")
                print(f"Fixed: {fixed_code}")
                print("-" * 40)
                
                success_count += 1
                
            except Exception as e:
                print(f"❌ Error applying fix: {str(e)}")
        
        # Return True if at least one fix was applied successfully
        return success_count > 0

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
