# MCP PHPStan Integration TUI Guide

This guide explains how to use the Text User Interface (TUI) for the MCP PHPStan Integration tool.

## Prerequisites

Before using the TUI, make sure you have:

1. Python 3.8+ installed
2. PHPStan installed in your PHP project
3. Claude API key set up in your environment

## Setting Up Your API Key

The TUI requires a Claude API key to communicate with Claude Code. You can set it up in two ways:

### Using .env File (Recommended)

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the .env file and add your Claude API key:
   ```bash
   # Open the file in your favorite editor
   nano .env
   
   # Add your API key
   CLAUDE_API_KEY=your_api_key_here
   ```

### Using Environment Variables

Alternatively, you can set the API key as an environment variable:

```bash
export CLAUDE_API_KEY=your_api_key_here
```

## Starting the TUI

The easiest way to start the TUI is using the provided script:

```bash
./run_tui.sh /path/to/your/php/project
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

Examples:

```bash
# Run with default settings
./run_tui.sh /path/to/php/project

# Run with 5 errors per batch and 20 maximum iterations
./run_tui.sh /path/to/php/project --max-errors 5 --max-iterations 20

# Run in simple CLI mode (useful for small terminals or SSH)
./run_tui.sh /path/to/php/project --simple

# Run in verbose mode
./run_tui.sh /path/to/php/project --verbose
```

## TUI Controls

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

## Views

### Errors View

The errors view shows the current batch of errors detected by PHPStan. It displays:

- The batch number and total number of batches
- The files containing errors
- The line numbers and error messages

### Log View

The log view shows a chronological log of actions taken by the TUI, including:

- PHPStan analysis runs
- Error detection
- Communication with Claude
- Fix application

### Help View

The help view shows a summary of available keyboard controls and commands.

## Command Mode

You can enter command mode by pressing `:`. In command mode, you can enter the following commands:

- **:run**: Run PHPStan analysis
- **:fix**: Fix current batch of errors
- **:fixall**: Fix all batches of errors
- **:next**: Next batch of errors
- **:prev**: Previous batch of errors
- **:quit**: Quit
- **:help**: Show help

## Simple CLI Interface

If you're working in an environment where the TUI doesn't work well (like a small terminal or over SSH), you can use the simple CLI interface:

```bash
./run_tui.sh /path/to/your/php/project --simple
```

The simple CLI interface provides the same functionality as the TUI but with a simpler interface that works in any terminal.

## Workflow Example

Here's a typical workflow for using the TUI:

1. Start the TUI:
   ```bash
   ./run_tui.sh /path/to/your/php/project
   ```

2. Press `r` to run PHPStan analysis on your project

3. View the detected errors in the errors view

4. Press `f` to fix the current batch of errors using Claude

5. Review the fixes in the log view (press `l` to switch to this view)

6. Press `n` to move to the next batch of errors

7. Repeat steps 4-6 until all errors are fixed, or press `a` to fix all batches automatically

8. Press `q` to quit when done

## Troubleshooting

### TUI Not Displaying Correctly

If the TUI doesn't display correctly:

1. Try increasing your terminal size
2. Use the simple CLI interface instead:
   ```bash
   ./run_tui.sh /path/to/your/php/project --simple
   ```

### API Key Issues

If you see an error about the Claude API key:

1. Make sure you've set up your API key correctly in the `.env` file or as an environment variable
2. Check that the API key is valid
3. If using the `.env` file, make sure it's in the correct location (the root of the mcp-phpstan directory)

### PHPStan Not Found

If PHPStan is not found:

1. Make sure PHPStan is installed in your PHP project:
   ```bash
   composer require --dev phpstan/phpstan
   ```
2. Check that the PHPStan binary is accessible from your project

### Claude Not Responding

If Claude is not responding:

1. Check your internet connection
2. Verify that your Claude API key is valid
3. Try again later (Claude API might be experiencing high traffic)
