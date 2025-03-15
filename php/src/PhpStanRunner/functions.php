<?php

namespace MCP\PHPStan\PhpStanRunner;

/**
 * Run PHPStan on a project and optionally save the output to a file
 *
 * @param string $projectPath Path to the PHP project
 * @param string|null $outputFile Path to save the output (if null, output is just returned)
 * @param array|null $paths List of paths to analyze
 * @param int|null $level PHPStan rule level (0-9)
 * @param string|null $configPath Path to PHPStan config file
 * @param bool $verbose Whether to run in verbose mode
 * @return array{0: string, 1: int} Tuple of (output, return_code)
 */
function runPhpstan(
    string $projectPath,
    ?string $outputFile = null,
    ?array $paths = null,
    ?int $level = null,
    ?string $configPath = null,
    bool $verbose = false
): array {
    $runner = new PhpStanRunner($projectPath);
    
    // Check if PHPStan is installed
    if (!$runner->checkInstallation()) {
        $errorMsg = 
            "PHPStan is not installed or not found at the expected location. " .
            "Please run 'composer require --dev phpstan/phpstan' in your project.";
        
        if ($outputFile) {
            file_put_contents($outputFile, $errorMsg);
        }
        
        return [$errorMsg, 1];
    }
    
    // Run the analysis
    list($output, $returnCode) = $runner->runAnalysis($paths, $level, $configPath, $verbose);
    
    // Save to file if requested
    if ($outputFile) {
        file_put_contents($outputFile, $output);
    }
    
    return [$output, $returnCode];
}
