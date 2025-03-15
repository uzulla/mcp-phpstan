<?php

require_once __DIR__ . '/vendor/autoload.php';

use MCP\PHPStan\IncrementalProcessor;

// Path to the sample PHP project
$projectPath = __DIR__ . '/../samples/php_project';

// Create a processor
$processor = new IncrementalProcessor(
    $projectPath,
    max_errors_per_batch: 2,
    max_iterations: 2,
    verbose: true
);

// Run the processor in dry-run mode
echo "Running PHPStan analysis with MCP integration...\n";
$processor->process();

// Print stats
echo "\nProcessor stats:\n";
echo json_encode($processor->getStats(), JSON_PRETTY_PRINT) . "\n";

echo "\nDemo completed successfully!\n";
