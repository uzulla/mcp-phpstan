# Using Claude Code with MCP for PHPStan Integration

This guide explains how to use Claude Code with the MCP PHPStan Integration tool to automatically fix PHP code errors.

## What is Claude Code?

Claude Code is Anthropic's code-focused AI assistant that can help you write, understand, and fix code. When combined with MCP (Model Context Protocol), Claude Code can interact with external tools like our PHPStan integration to automatically fix errors in your PHP code.

## Setting Up Claude Code with MCP

To use Claude Code with our MCP PHPStan Integration tool, you need to:

1. Have access to Claude Code
2. Configure Claude Code to use the MCP protocol
3. Connect Claude Code to our PHPStan integration

### API Key Setup

The tool requires a Claude API key to communicate with Claude. You can set it in the `.env` file:

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file and add your API key
# Replace 'your_api_key_here' with your actual API key
echo "CLAUDE_API_KEY=your_api_key_here" >> .env
```

Alternatively, you can set it as an environment variable:

```bash
export CLAUDE_API_KEY=your_api_key_here
```

## Using the TUI Interface

Our tool provides a Text User Interface (TUI) that makes it easy to interact with Claude Code via MCP. The TUI allows you to:

1. Run PHPStan analysis on your PHP project
2. View detected errors
3. Send errors to Claude Code for fixing
4. Apply the suggested fixes
5. Track the progress of error fixing

### Starting the TUI

The easiest way to start the TUI interface is using the provided script:

```bash
./run_tui.sh /path/to/your/php/project
```

Or you can run it directly:

```bash
python3 src/TuiInterface/tui_client.py /path/to/your/php/project
```

### Command-Line Options

The `run_tui.sh` script supports the following options:

```bash
./run_tui.sh /path/to/php/project [options]

Options:
  --max-errors N      Maximum errors per batch (default: 3)
  --max-iterations N  Maximum iterations (default: 10)
  --simple            Use simple CLI interface instead of TUI
  --verbose           Run in verbose mode
```

### TUI Controls

The TUI provides the following keyboard controls:

- **e**: Show errors view
- **l**: Show log view
- **h**: Show help
- **q**: Quit
- **:** : Enter command mode
- **n**: Next batch of errors
- **p**: Previous batch of errors
- **r**: Run PHPStan analysis
- **f**: Fix current batch of errors
- **a**: Fix all batches of errors

### Command Mode

In command mode (accessed by pressing `:` ), you can enter the following commands:

- **:run**: Run PHPStan analysis
- **:fix**: Fix current batch of errors
- **:fixall**: Fix all batches of errors
- **:next**: Next batch of errors
- **:prev**: Previous batch of errors
- **:quit**: Quit
- **:help**: Show help

### Simple CLI Interface

If you're working in an environment where the TUI doesn't work well (like a small terminal or over SSH), you can use the simple CLI interface:

```bash
./run_tui.sh /path/to/your/php/project --simple
```

Or run it directly:

```bash
python3 src/TuiInterface/simple_client.py /path/to/your/php/project
```

## Workflow Example

Here's a typical workflow for using Claude Code with our MCP PHPStan Integration tool:

1. Set your Claude API key in the `.env` file or as an environment variable:
   ```bash
   # Either copy and edit .env file
   cp .env.example .env
   # Edit .env and add your API key
   
   # Or set environment variable directly
   export CLAUDE_API_KEY=your_api_key_here
   ```

2. Start the TUI interface:
   ```bash
   ./run_tui.sh /path/to/your/php/project
   ```

3. Press `r` to run PHPStan analysis on your project

4. View the detected errors in the errors view (press `e` if not already in this view)

5. Press `f` to fix the current batch of errors using Claude Code

6. Review the fixes in the log view (press `l` to switch to this view)

7. Press `n` to move to the next batch of errors

8. Repeat steps 5-7 until all errors are fixed, or press `a` to fix all batches automatically

9. Press `q` to quit when done

## Integrating with Claude Code MCP

To integrate this tool with Claude Code's MCP system:

1. Load the MCP extension in Claude Code
2. Configure the MCP extension to use the PHPStan integration
3. Use the TUI to interact with Claude Code via MCP

### MCP Configuration

The MCP configuration for Claude Code should include:

```json
{
  "name": "phpstan-mcp",
  "description": "PHPStan integration for fixing PHP code errors",
  "version": "1.0.0",
  "commands": [
    {
      "name": "run_phpstan",
      "description": "Run PHPStan analysis on a PHP project",
      "parameters": {
        "project_path": {
          "type": "string",
          "description": "Path to the PHP project"
        }
      }
    },
    {
      "name": "fix_errors",
      "description": "Fix errors detected by PHPStan",
      "parameters": {
        "batch_index": {
          "type": "integer",
          "description": "Index of the batch to fix"
        }
      }
    }
  ]
}
```

## Troubleshooting

### Claude Code Not Responding

If Claude Code is not responding:

1. Check your internet connection
2. Verify that your Claude API key is valid and properly set:
   ```bash
   echo $CLAUDE_API_KEY
   ```
3. Check that Claude Code is properly configured for MCP

### Fixes Not Being Applied

If Claude Code suggests fixes but they're not being applied:

1. Check the log view for error messages
2. Verify that the file paths in the fixes match your project structure
3. Check that the files are writable

### PHPStan Not Finding Errors

If PHPStan is not finding errors:

1. Check that PHPStan is properly installed in your project:
   ```bash
   composer require --dev phpstan/phpstan
   ```
2. Verify that your PHPStan configuration is correct
3. Check that the paths you're analyzing contain PHP files

### TUI Display Issues

If the TUI doesn't display correctly:

1. Try increasing your terminal size
2. Use the simple CLI interface instead:
   ```bash
   ./run_tui.sh /path/to/your/php/project --simple
   ```

## Advanced Usage

### Customizing the TUI

You can customize the TUI by modifying the `TuiClient` class in `src/TuiInterface/tui_client.py`.

### Using Claude Code Directly

If you prefer to use Claude Code directly without the TUI, you can use the `McpClient` class in `src/McpIntegration/McpClient.py`:

```python
import os
import dotenv
from src.McpIntegration.McpClient import McpClient

# Load environment variables from .env file
dotenv.load_dotenv()

# Or set API key directly (not recommended for production)
# os.environ["CLAUDE_API_KEY"] = "your_api_key_here"

# Initialize MCP client
client = McpClient("/path/to/your/php/project")

# Run PHPStan analysis
output, return_code, batches = client.run_phpstan_analysis()

# Process errors
for batch in batches:
    message = client.prepare_mcp_message(batch)
    response = client.send_to_claude(message)
    client.apply_fixes(response["fixes"])
```

## Further Resources

- [Claude Code Documentation](https://docs.anthropic.com/claude/docs)
- [MCP Documentation](https://github.com/auchenberg/claude-code-mcp)
- [PHPStan Documentation](https://phpstan.org/user-guide/getting-started)
