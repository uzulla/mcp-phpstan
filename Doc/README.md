# MCP PHPStan Integration

This tool integrates PHPStan with Claude Code via the Model Context Protocol (MCP) to automatically fix PHP code errors detected by PHPStan.

## Overview

The MCP PHPStan Integration tool:

1. Runs PHPStan on your PHP project to detect errors
2. Formats the errors into batches
3. Sends these batches to Claude Code via MCP
4. Applies the fixes suggested by Claude
5. Repeats the process until all errors are fixed or a maximum number of iterations is reached

The tool processes errors incrementally, handling a small batch at a time to prevent overwhelming the MCP with too many errors at once.

## Installation

### Prerequisites

- PHP 7.4+
- Composer
- PHPStan installed in your PHP project
- Access to Claude Code with MCP support

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/uzulla/mcp-phpstan.git
   cd mcp-phpstan
   ```

2. Install PHPStan in your PHP project if not already installed:
   ```bash
   cd your-php-project
   composer require --dev phpstan/phpstan
   ```

3. Configure PHPStan for your project (if not already configured):
   ```bash
   # Create a basic PHPStan configuration
   echo "parameters:
     level: 5
     paths:
       - src" > phpstan.neon
   ```

## Usage

### Basic Usage

Run the tool on your PHP project:

```bash
php php/src/main.php /path/to/your/php/project
```

### Advanced Options

```bash
php php/src/main.php /path/to/your/php/project [options]
```

Options:
- `--paths`, `-p`: Specify paths to analyze (defaults to paths in phpstan.neon)
- `--level`, `-l`: PHPStan rule level (0-9, defaults to level in phpstan.neon)
- `--config`, `-c`: Path to PHPStan config file (defaults to phpstan.neon in project root)
- `--verbose`, `-v`: Run in verbose mode
- `--max-errors`, `-m`: Maximum errors per batch (default: 3)
- `--max-iterations`, `-i`: Maximum iterations to run (default: 10)
- `--dry-run`: Run without applying fixes (for testing)

### Incremental Processing

For more control over the incremental processing:

```bash
php php/src/IncrementalProcessor.php /path/to/your/php/project [options]
```

Options:
- Same as main.py, plus:
- `--stats-file`: Path to save statistics to

## How It Works

### 1. PHPStan Analysis

The tool runs PHPStan on your PHP project to detect errors. PHPStan is a static analysis tool that finds errors in your PHP code without actually running it.

### 2. Error Formatting

The detected errors are formatted into batches of a configurable size (default: 3 errors per batch). This prevents overwhelming the MCP with too many errors at once.

### 3. MCP Integration

Each batch of errors is sent to Claude Code via MCP. The message includes:
- The errors in the batch
- The file contents where the errors occur
- Batch information (index, total errors, etc.)

### 4. Fix Application

Claude analyzes the errors and suggests fixes. The tool applies these fixes to your PHP code.

### 5. Iteration

The process repeats until all errors are fixed or a maximum number of iterations is reached.

## Configuration

You can configure the tool's behavior using command-line options or by modifying the source code.

### PHPStan Configuration

The tool uses your project's PHPStan configuration (phpstan.neon) by default. You can specify a different configuration file using the `--config` option.

### Batch Size

You can adjust the number of errors processed in each batch using the `--max-errors` option. A smaller batch size may result in more accurate fixes but will require more iterations.

### Maximum Iterations

You can limit the number of iterations using the `--max-iterations` option. This prevents the tool from running indefinitely if it cannot fix all errors.

## Troubleshooting

### PHPStan Not Found

If the tool cannot find PHPStan, make sure it's installed in your PHP project:

```bash
composer require --dev phpstan/phpstan
```

### Claude Not Suggesting Fixes

If Claude is not suggesting fixes for certain errors, try:
- Reducing the batch size
- Providing more context (e.g., including more of the file contents)
- Simplifying the errors (e.g., fixing some errors manually first)

### Fixes Not Working

If the suggested fixes are not resolving the errors, try:
- Running in verbose mode to see more details
- Checking the PHPStan output manually
- Fixing some errors manually to simplify the problem

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
