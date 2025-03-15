# Claude Code MCP Commands for PHPStan Integration

This document describes the MCP commands available for the PHPStan Integration tool when used with Claude Code.

## Overview

The PHPStan Integration tool provides the following MCP commands for Claude Code:

1. `run_phpstan`: Run PHPStan analysis on a PHP project
2. `fix_errors`: Fix errors detected by PHPStan
3. `list_errors`: List errors detected by PHPStan
4. `select_errors`: Select specific errors to fix

## Command Details

### run_phpstan

Run PHPStan analysis on a PHP project.

**Parameters:**
- `project_path` (string, required): Path to the PHP project
- `paths` (array of strings, optional): Paths to analyze
- `level` (integer, optional): PHPStan rule level (0-9)
- `config_path` (string, optional): Path to PHPStan config file
- `verbose` (boolean, optional): Whether to run in verbose mode

**Example:**
```
/mcp phpstan-mcp run_phpstan --project_path=/path/to/php/project
```

**Response:**
```json
{
  "status": "success",
  "message": "Found 5 errors in 2 batches:",
  "errors": 5,
  "batches": 2,
  "all_errors": [
    {
      "file": "src/Models/User.php",
      "line": 42,
      "message": "Method User::getEmail() should return string but returns string|null.",
      "index": 0
    },
    ...
  ],
  "too_many_errors": false
}
```

If there are more than 10 errors, only the first 10 will be shown:

```json
{
  "status": "success",
  "message": "Found 15 errors in 5 batches. Showing first 10 errors:",
  "errors": 15,
  "batches": 5,
  "first_10_errors": [
    {
      "file": "src/Models/User.php",
      "line": 42,
      "message": "Method User::getEmail() should return string but returns string|null.",
      "index": 0
    },
    ...
  ],
  "too_many_errors": true
}
```

### fix_errors

Fix errors detected by PHPStan.

**Parameters:**
- `batch_index` (integer, optional): Index of the batch to fix
- `error_indices` (array of integers, optional): Indices of errors to fix

**Example:**
```
/mcp phpstan-mcp fix_errors --batch_index=0 --error_indices=[0,1,2]
```

**Response:**
```json
{
  "status": "success",
  "message": "Applied 3 fixes successfully!",
  "fixes": [
    {
      "file": "src/Models/User.php",
      "line": 42,
      "original_code": "public function getEmail(): string",
      "fixed_code": "public function getEmail(): ?string",
      "explanation": "Changed return type to ?string to match the actual return value which can be null."
    },
    ...
  ],
  "remaining_errors": 2,
  "fixed_errors": 3,
  "all_fixed": false
}
```

### list_errors

List errors detected by PHPStan.

**Parameters:**
- `batch_index` (integer, optional): Index of the batch to list
- `max_errors` (integer, optional): Maximum number of errors to list

**Example:**
```
/mcp phpstan-mcp list_errors --batch_index=0 --max_errors=5
```

**Response:**
```json
{
  "status": "success",
  "message": "Listing errors for batch 1/2:",
  "errors": [
    {
      "file": "src/Models/User.php",
      "line": 42,
      "message": "Method User::getEmail() should return string but returns string|null.",
      "index": 0
    },
    ...
  ],
  "batch_index": 0,
  "total_batches": 2
}
```

### select_errors

Select specific errors to fix.

**Parameters:**
- `batch_index` (integer, optional): Index of the batch to select from
- `error_indices` (array of integers, required): Indices of errors to select

**Example:**
```
/mcp phpstan-mcp select_errors --batch_index=0 --error_indices=[0,2]
```

**Response:**
```json
{
  "status": "success",
  "message": "Selected 2 errors for fixing:",
  "selected_errors": [
    {
      "file": "src/Models/User.php",
      "line": 42,
      "message": "Method User::getEmail() should return string but returns string|null.",
      "index": 0
    },
    {
      "file": "src/Models/User.php",
      "line": 56,
      "message": "Parameter #1 $id of method User::find() expects int, string given.",
      "index": 2
    }
  ],
  "batch_index": 0
}
```

## Using MCP Commands in Claude Code

To use these commands in Claude Code, you need to:

1. Load the MCP extension in Claude Code
2. Configure the MCP extension to use the PHPStan integration
3. Use the MCP commands in your conversation with Claude Code

### Example Workflow

Here's an example workflow for using the PHPStan Integration with Claude Code:

1. Run PHPStan analysis:
   ```
   /mcp phpstan-mcp run_phpstan --project_path=/path/to/php/project
   ```

2. If there are too many errors, list the first batch:
   ```
   /mcp phpstan-mcp list_errors --batch_index=0 --max_errors=10
   ```

3. Select specific errors to fix:
   ```
   /mcp phpstan-mcp select_errors --batch_index=0 --error_indices=[0,2,3]
   ```

4. Fix the selected errors:
   ```
   /mcp phpstan-mcp fix_errors --batch_index=0
   ```

5. Repeat steps 2-4 until all errors are fixed.

## Troubleshooting

### Command Not Found

If Claude Code reports that the command is not found, make sure that:

1. The MCP extension is properly loaded in Claude Code
2. The MCP extension is configured to use the PHPStan integration
3. You're using the correct command syntax

### No Errors Found

If PHPStan doesn't find any errors, make sure that:

1. The project path is correct
2. PHPStan is properly installed in the project
3. The project contains PHP files with errors

### Fixes Not Applied

If Claude Code suggests fixes but they're not applied, make sure that:

1. The file paths in the fixes match your project structure
2. The files are writable
3. The original code in the fixes matches the code in the files

## Further Resources

- [Claude Code Documentation](https://docs.anthropic.com/claude/docs)
- [MCP Documentation](https://github.com/auchenberg/claude-code-mcp)
- [PHPStan Documentation](https://phpstan.org/user-guide/getting-started)
