# MCP PHPStan Integration Architecture

This document describes the architecture of the MCP PHPStan Integration tool, which connects PHPStan with Claude Code via MCP to automatically fix PHP code errors.

## System Overview

The system consists of several modular components that work together:

1. **PHPStan Runner**: Executes PHPStan on PHP projects and captures the output
2. **Error Formatter**: Parses PHPStan output and formats errors for MCP
3. **MCP Client**: Handles communication with Claude Code via MCP
4. **Incremental Processor**: Orchestrates the entire process, handling errors in batches

## Component Details

### PHPStan Runner (`src/PhpStanRunner/Runner.py`)

This component is responsible for:
- Running PHPStan on PHP projects
- Capturing and returning the output
- Checking if PHPStan is properly installed

Key classes and functions:
- `PhpStanRunner`: Class that runs PHPStan and captures the output
- `run_phpstan()`: Function that runs PHPStan and optionally saves the output to a file

### Error Formatter (`src/ErrorFormatter/Formatter.py`)

This component is responsible for:
- Parsing PHPStan output to extract errors
- Formatting errors into a structure suitable for MCP
- Batching errors to prevent overwhelming the MCP

Key classes and functions:
- `PhpStanError`: Class representing a single PHPStan error
- `PhpStanErrorFormatter`: Class that formats PHPStan errors for MCP
- `format_phpstan_output()`: Function that formats PHPStan output for MCP

### MCP Client (`src/McpIntegration/McpClient.py`)

This component is responsible for:
- Preparing messages for Claude Code via MCP
- Sending messages to Claude
- Applying fixes suggested by Claude

Key classes and functions:
- `McpClient`: Class for interacting with Claude Code via MCP
- `prepare_mcp_message()`: Method that prepares a message for Claude
- `send_to_claude()`: Method that sends a message to Claude
- `apply_fixes()`: Method that applies fixes suggested by Claude

### Incremental Processor (`src/incremental_processor.py`)

This component is responsible for:
- Orchestrating the entire process
- Processing errors incrementally in batches
- Tracking statistics about the processing

Key classes and functions:
- `IncrementalProcessor`: Class that processes PHPStan errors incrementally
- `process()`: Method that processes PHPStan errors incrementally
- `get_stats()`: Method that returns statistics about the processing

### Main Entry Point (`src/main.py`)

This component is responsible for:
- Parsing command-line arguments
- Initializing the MCP client
- Running the appropriate functionality based on the arguments

Key functions:
- `parse_args()`: Function that parses command-line arguments
- `main()`: Main entry point for the tool

## Data Flow

1. The user runs the tool on a PHP project
2. The PHPStan Runner executes PHPStan and captures the output
3. The Error Formatter parses the output and formats errors into batches
4. For each batch:
   a. The MCP Client prepares a message for Claude
   b. The message is sent to Claude via MCP
   c. Claude suggests fixes
   d. The MCP Client applies the fixes
5. The process repeats until all errors are fixed or a maximum number of iterations is reached

## Error Batching

To prevent overwhelming the MCP with too many errors at once, the tool processes errors in batches. The batch size is configurable (default: 3 errors per batch).

Each batch includes:
- The errors in the batch
- The file contents where the errors occur
- Batch information (index, total errors, etc.)

## Incremental Processing

The tool processes errors incrementally, handling a small batch at a time. This approach has several advantages:
- It prevents overwhelming the MCP with too many errors at once
- It allows for more focused fixes
- It provides better feedback to the user about the progress

The incremental processing works as follows:
1. Run PHPStan to detect errors
2. Process a batch of errors
3. Apply fixes
4. Run PHPStan again to check if the fixes worked
5. Repeat until all errors are fixed or a maximum number of iterations is reached

## Extension Points

The tool is designed to be extensible. Here are some potential extension points:

### Supporting Other Static Analysis Tools

The architecture could be extended to support other static analysis tools besides PHPStan. This would involve:
- Creating a new runner for the tool
- Creating a new error formatter for the tool's output
- Updating the MCP client to handle the new error format

### Supporting Other LLMs

The architecture could be extended to support other LLMs besides Claude. This would involve:
- Creating a new client for the LLM
- Updating the MCP client to use the new LLM client

### Adding More Fix Strategies

The architecture could be extended to support more fix strategies. This would involve:
- Updating the MCP client to support the new strategies
- Updating the incremental processor to use the new strategies

## Future Improvements

Potential future improvements include:
- Adding support for other static analysis tools
- Adding support for other LLMs
- Improving the fix strategies
- Adding a GUI or web interface
- Adding more detailed reporting and visualization of the fixes
- Implementing parallel processing of batches
- Adding support for custom fix templates
