# Makefile for MCP-PHPStan testing

.PHONY: setup test reset demo clean

# Setup the test environment
setup:
	@echo "Setting up test environment..."
	@cd samples && composer require --dev phpstan/phpstan
	@cd php && composer install

# Reset the sample project to its problematic state
reset:
	@echo "Resetting sample project to problematic state..."
	@rm -rf samples/php_project/src
	@cp -r samples/ProblemExample/src samples/php_project/
	@echo "Reset complete. Sample project now contains PHPStan errors."

# Run PHPStan on the sample project
test:
	@echo "Running PHPStan on sample project..."
	@cd samples && ./vendor/bin/phpstan analyse php_project/src/ --level=5 || true

# Run the demo script to fix errors
demo:
	@echo "Running demo script to fix PHPStan errors..."
	@cd php && php demo.php

# Full test cycle: reset, test, demo, test
full-test: reset test demo test

# Clean up
clean:
	@echo "Cleaning up..."
	@rm -rf samples/vendor
	@rm -rf php/vendor
	@rm -f samples/composer.lock
	@echo "Cleanup complete."
