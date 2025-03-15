# Sample PHP Project with PHPStan Errors

This is a sample PHP project that contains intentional errors for PHPStan to detect.
The errors include:

- Undefined variables
- Type mismatches
- Missing return types
- Uninitialized properties
- Calling undefined methods
- Method calls on non-objects
- Undefined classes
- Unused parameters
- And more...

## Running PHPStan

To run PHPStan on this project:

```bash
# Install dependencies
composer install

# Run PHPStan analysis
vendor/bin/phpstan analyse
```

The errors detected by PHPStan will be displayed in the console output.
