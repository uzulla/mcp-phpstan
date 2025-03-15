# MCP PHPStan Integration

This project provides integration between PHPStan and Claude Code via MCP (Multi-agent Conversation Protocol).

## Migration from Python to PHP

This project was originally implemented in Python and has been migrated to PHP. The PHP implementation maintains the same functionality as the Python implementation, including:

- Running PHPStan analysis on PHP projects
- Formatting PHPStan errors for Claude Code via MCP
- Sending errors to Claude for analysis
- Applying suggested fixes to PHP files
- Tracking error statistics

The migration ensures that all functionality from the Python implementation is preserved in the PHP implementation, making it easier to use in PHP projects without requiring Python.

## Installation

To use the PHP implementation, you need:

- PHP 7.4+
- Composer
- PHPStan installed in your PHP project

## Usage

See the documentation in the `Doc` directory for detailed usage instructions.
