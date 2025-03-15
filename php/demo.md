# MCP PHPStan Integration Demo

This document demonstrates how to use the MCP PHPStan Integration tool to automatically fix PHPStan errors with Claude Code.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/uzulla/mcp-phpstan.git
   cd mcp-phpstan/php
   ```

2. Install dependencies:
   ```bash
   composer install
   ```

3. Configure your Claude API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your Claude API key
   ```

## Basic Usage

Run the tool on a PHP project:

```bash
php src/main.php /path/to/your/php/project
```

### Command-line Options

```
Usage: php src/main.php <project_path> [options]

PHPStan Options:
  --paths, -p <paths>       Paths to analyze (defaults to paths in phpstan.neon)
  --level, -l <level>       PHPStan rule level (0-9, defaults to level in phpstan.neon)
  --config, -c <file>       Path to PHPStan config file (defaults to phpstan.neon in project root)
  --verbose, -v             Run PHPStan in verbose mode

MCP Options:
  --max-errors, -m <num>    Maximum errors per batch (default: 3)
  --max-iterations, -i <num> Maximum iterations to run (default: 10)
  --dry-run                 Run without applying fixes (for testing)
```

## Example Output

Running the tool on a sample PHP project:

```bash
$ php src/main.php ../samples/php_project --verbose

Running PHPStan analysis...
PHPStan analysis completed with errors. Found 2 batches.

Preparing MCP message for first batch:
{
  "type": "mcp_phpstan_errors",
  "batch_info": {
    "index": 0,
    "total_errors": 3,
    "batch_size": 2,
    "has_more": true
  },
  "errors": {
    "src/Models/User.php": [
      {
        "message": "Property User::$email type has no value type specified in iterable type array.",
        "file": "src/Models/User.php",
        "line": 15,
        "error_type": "missing_type"
      }
    ],
    "src/Controllers/UserController.php": [
      {
        "message": "Call to method save() on an unknown class User.",
        "file": "src/Controllers/UserController.php",
        "line": 42,
        "error_type": "not_found"
      }
    ]
  },
  "file_contents": {
    "src/Models/User.php": "<?php\n\nclass User {\n    private $email = [];\n    \n    public function validateEmail($email) {\n        // Validation logic\n    }\n}\n",
    "src/Controllers/UserController.php": "<?php\n\nclass UserController {\n    public function store() {\n        $user = new User();\n        $user->save();\n    }\n}\n"
  },
  "project_path": "/path/to/project"
}

Simulating sending to Claude...

Mock response from Claude:
{
  "status": "success",
  "message": "This is a mock response. In a real implementation, this would be Claude's response.",
  "fixes": [
    {
      "file": "src/Models/User.php",
      "line": 15,
      "original": "private $email = [];",
      "fixed": "private array $email = [];"
    },
    {
      "file": "src/Controllers/UserController.php",
      "line": 42,
      "original": "$user->save();",
      "fixed": "// User class doesn't have a save method\n// Either implement the method or use a different approach\n// $user->save();"
    }
  ]
}

Applying fixes suggested by Claude...
Fixed 2 errors in iteration 1
```

## Running Tests

To run the PHPUnit tests:

```bash
cd php
vendor/bin/phpunit
```

## Integration with Claude API

The tool uses Claude's API to suggest fixes for PHPStan errors. The integration works as follows:

1. PHPStan is run on the PHP project to identify errors
2. Errors are formatted and sent to Claude in batches
3. Claude analyzes the errors and suggests fixes
4. The fixes are applied to the PHP files
5. The process repeats until all errors are fixed or the maximum number of iterations is reached

The Claude API key is stored in the `.env` file and is not committed to the repository.
