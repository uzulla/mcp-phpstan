<?php

namespace MCP\PHPStan;

use MCP\PHPStan\McpIntegration\McpClient;

/**
 * Main entry point for the MCP PHPStan integration.
 *
 * This script provides a command-line interface for running the MCP PHPStan integration.
 * It handles parsing command-line arguments and running the appropriate functionality.
 */

/**
 * Parse command-line arguments
 *
 * @param array $argv Command line arguments
 * @return array Parsed arguments
 */
function parseArgs(array $argv): array
{
    // Default values
    $args = [
        'project_path' => null,
        'paths' => null,
        'level' => null,
        'config' => null,
        'verbose' => false,
        'max_errors' => 3,
        'max_iterations' => 10,
        'dry_run' => false
    ];
    
    // Check if project path is provided
    if (isset($argv[1]) && !str_starts_with($argv[1], '-')) {
        $args['project_path'] = $argv[1];
    } else {
        echo "Error: Project path is required\n";
        echo "Usage: php main.php <project_path> [options]\n";
        exit(1);
    }
    
    // Parse command line arguments
    for ($i = 2; $i < count($argv); $i++) {
        switch ($argv[$i]) {
            case '--paths':
            case '-p':
                $args['paths'] = [];
                $i++;
                while ($i < count($argv) && !str_starts_with($argv[$i], '-')) {
                    $args['paths'][] = $argv[$i];
                    $i++;
                }
                $i--; // Adjust for the outer loop increment
                break;
                
            case '--level':
            case '-l':
                $args['level'] = (int)$argv[++$i];
                break;
                
            case '--config':
            case '-c':
                $args['config'] = $argv[++$i];
                break;
                
            case '--verbose':
            case '-v':
                $args['verbose'] = true;
                break;
                
            case '--max-errors':
            case '-m':
                $args['max_errors'] = (int)$argv[++$i];
                break;
                
            case '--max-iterations':
            case '-i':
                $args['max_iterations'] = (int)$argv[++$i];
                break;
                
            case '--dry-run':
                $args['dry_run'] = true;
                break;
        }
    }
    
    return $args;
}

/**
 * Main entry point
 *
 * @param array $argv Command line arguments
 * @return int Exit code
 */
function main(array $argv): int
{
    // Parse command-line arguments
    $args = parseArgs($argv);
    
    // Initialize MCP client
    $client = new McpClient(
        $args['project_path'],
        $args['max_errors']
    );
    
    // If dry run, just analyze and print
    if ($args['dry_run']) {
        echo "Running in dry-run mode (no fixes will be applied)\n";
        
        // Run PHPStan analysis
        list($output, $returnCode, $batches) = $client->runPhpstanAnalysis(
            $args['paths'],
            $args['level'],
            $args['config'],
            $args['verbose']
        );
        
        // Print results
        if ($returnCode === 0) {
            echo "No PHPStan errors found\n";
            return 0;
        }
        
        $totalErrors = array_sum(array_map(function($batch) {
            return $batch['batch']['batch_size'];
        }, $batches));
        
        echo "Found {$totalErrors} errors in " . count($batches) . " batches\n";
        
        // Print first batch as example
        if (!empty($batches)) {
            echo "\nExample batch:\n";
            foreach ($batches[0]['errors_by_file'] as $filePath => $errors) {
                echo "\nFile: {$filePath}\n";
                foreach ($errors as $error) {
                    echo "  Line {$error['line']}: {$error['message']}\n";
                }
            }
        }
        
        return 1;
    }
    
    // Process PHPStan errors
    $success = $client->processPhpstanErrors(
        $args['paths'],
        $args['level'],
        $args['config'],
        $args['verbose'],
        $args['max_iterations']
    );
    
    return $success ? 0 : 1;
}

// Only run main when script is executed directly
if (isset($argv[0]) && basename($argv[0]) === basename(__FILE__)) {
    exit(main($argv));
}
