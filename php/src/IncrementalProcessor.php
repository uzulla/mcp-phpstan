<?php

namespace MCP\PHPStan;

use MCP\PHPStan\PhpStanRunner\PhpStanRunner;
use MCP\PHPStan\ErrorFormatter\PhpStanErrorFormatter;
use MCP\PHPStan\McpIntegration\McpClient;

/**
 * Incremental PHPStan Error Processor
 *
 * This class provides functionality to incrementally process PHPStan errors
 * with Claude Code via MCP, processing a few errors at a time until all are fixed.
 */
class IncrementalProcessor
{
    private string $projectPath;
    private int $maxErrorsPerBatch;
    private int $maxIterations;
    private bool $verbose;
    private McpClient $mcpClient;
    private PhpStanRunner $phpstanRunner;
    private PhpStanErrorFormatter $errorFormatter;
    private array $stats;

    /**
     * Initialize the incremental processor
     *
     * @param string $projectPath Path to the PHP project
     * @param int $maxErrorsPerBatch Maximum number of errors to process in a single batch
     * @param int $maxIterations Maximum number of iterations to run
     * @param string|null $phpstanBinary Path to the PHPStan binary
     * @param bool $verbose Whether to run in verbose mode
     */
    public function __construct(
        string $projectPath,
        int $maxErrorsPerBatch = 3,
        int $maxIterations = 10,
        ?string $phpstanBinary = null,
        bool $verbose = false
    ) {
        $this->projectPath = realpath($projectPath);
        $this->maxErrorsPerBatch = $maxErrorsPerBatch;
        $this->maxIterations = $maxIterations;
        $this->verbose = $verbose;
        
        // Initialize MCP client
        $this->mcpClient = new McpClient($projectPath, $maxErrorsPerBatch, $phpstanBinary);
        
        // Initialize PHPStan runner
        $this->phpstanRunner = new PhpStanRunner($projectPath, $phpstanBinary);
        
        // Initialize error formatter
        $this->errorFormatter = new PhpStanErrorFormatter($maxErrorsPerBatch);
        
        // Statistics
        $this->stats = [
            'iterations' => 0,
            'total_errors_fixed' => 0,
            'total_batches_processed' => 0,
            'errors_by_type' => []
        ];
    }

    /**
     * Process PHPStan errors incrementally
     *
     * @param array|null $paths List of paths to analyze
     * @param int|null $level PHPStan rule level (0-9)
     * @param string|null $configPath Path to PHPStan config file
     * @return bool True if all errors were fixed, False otherwise
     */
    public function process(?array $paths = null, ?int $level = null, ?string $configPath = null): bool
    {
        $iteration = 0;
        $totalErrorsFixed = 0;
        
        while ($iteration < $this->maxIterations) {
            echo "\n=== Iteration " . ($iteration + 1) . "/{$this->maxIterations} ===\n";
            
            // Run PHPStan analysis
            list($output, $returnCode, $batches) = $this->mcpClient->runPhpstanAnalysis(
                $paths, 
                $level, 
                $configPath, 
                $this->verbose
            );
            
            // If no errors, we're done
            if ($returnCode === 0) {
                echo "\n✅ All PHPStan errors fixed! Total fixed: {$totalErrorsFixed}\n";
                $this->stats['iterations'] = $iteration + 1;
                $this->stats['total_errors_fixed'] = $totalErrorsFixed;
                return true;
            }
            
            // Get total errors in this iteration
            $totalErrors = array_sum(array_map(function($batch) {
                return $batch['batch']['batch_size'];
            }, $batches));
            
            echo "Found {$totalErrors} errors in " . count($batches) . " batches\n";
            
            // Process batches one by one
            $errorsFixedThisIteration = 0;
            
            foreach ($batches as $batchIdx => $batch) {
                echo "\n--- Processing batch " . ($batchIdx + 1) . "/" . count($batches) . " ---\n";
                $batchSize = $batch['batch']['batch_size'];
                
                // Prepare MCP message with file contents
                $fileContents = $this->getFileContents(array_keys($batch['errors_by_file']));
                $message = $this->mcpClient->prepareMcpMessage($batch, $fileContents);
                
                // Send to Claude
                echo "Sending batch with {$batchSize} errors to Claude...\n";
                $response = $this->mcpClient->sendToClaude($message);
                
                // Apply fixes
                if (isset($response['fixes']) && !empty($response['fixes'])) {
                    $numFixes = count($response['fixes']);
                    echo "Applying {$numFixes} fixes suggested by Claude...\n";
                    
                    $success = $this->mcpClient->applyFixes($response['fixes']);
                    if ($success) {
                        $errorsFixedThisIteration += $numFixes;
                        $this->updateErrorStats($batch);
                    } else {
                        echo "❌ Failed to apply fixes\n";
                        return false;
                    }
                } else {
                    echo "⚠️ No fixes suggested by Claude for this batch\n";
                }
                
                // Update statistics
                $this->stats['total_batches_processed']++;
                
                // Optional: Add a delay between batches to avoid rate limiting
                if ($batchIdx < count($batches) - 1) {
                    sleep(1);
                }
            }
            
            // Update total errors fixed
            $totalErrorsFixed += $errorsFixedThisIteration;
            
            // If no errors were fixed in this iteration, we're stuck
            if ($errorsFixedThisIteration === 0) {
                echo "\n⚠️ No errors fixed in iteration " . ($iteration + 1) . ". Stopping.\n";
                $this->stats['iterations'] = $iteration + 1;
                $this->stats['total_errors_fixed'] = $totalErrorsFixed;
                return false;
            }
            
            echo "\nFixed {$errorsFixedThisIteration} errors in iteration " . ($iteration + 1) . "\n";
            echo "Total errors fixed so far: {$totalErrorsFixed}\n";
            
            // Increment iteration counter
            $iteration++;
        }
        
        // If we've reached max_iterations, we've failed to fix all errors
        echo "\n⚠️ Reached maximum iterations ({$this->maxIterations}) without fixing all errors\n";
        echo "Total errors fixed: {$totalErrorsFixed}\n";
        
        $this->stats['iterations'] = $this->maxIterations;
        $this->stats['total_errors_fixed'] = $totalErrorsFixed;
        
        return false;
    }

    /**
     * Get the contents of the specified files
     *
     * @param array $filePaths List of file paths
     * @return array Dictionary mapping file paths to their contents
     */
    private function getFileContents(array $filePaths): array
    {
        $fileContents = [];
        
        foreach ($filePaths as $filePath) {
            $fullPath = $this->projectPath . '/' . $filePath;
            if (file_exists($fullPath)) {
                try {
                    $fileContents[$filePath] = file_get_contents($fullPath);
                } catch (\Exception $e) {
                    echo "Error reading file {$filePath}: {$e->getMessage()}\n";
                }
            }
        }
        
        return $fileContents;
    }

    /**
     * Update error statistics
     *
     * @param array $batch Batch of errors
     */
    private function updateErrorStats(array $batch): void
    {
        foreach ($batch['errors_by_file'] as $filePath => $errors) {
            foreach ($errors as $error) {
                $errorType = $error['error_type'] ?? 'other';
                
                if (!isset($this->stats['errors_by_type'][$errorType])) {
                    $this->stats['errors_by_type'][$errorType] = 0;
                }
                
                $this->stats['errors_by_type'][$errorType]++;
            }
        }
    }

    /**
     * Get statistics about the processing
     *
     * @return array Dictionary of statistics
     */
    public function getStats(): array
    {
        return $this->stats;
    }
}

/**
 * Main entry point for the incremental processor
 *
 * @param array $argv Command line arguments
 * @return int Exit code
 */
function main(array $argv): int
{
    // Default values
    $projectPath = $argv[1] ?? null;
    $paths = null;
    $level = null;
    $configPath = null;
    $maxErrors = 3;
    $maxIterations = 10;
    $verbose = false;
    $statsFile = null;
    
    // Check if project path is provided
    if (!$projectPath) {
        echo "Error: Project path is required\n";
        echo "Usage: php IncrementalProcessor.php <project_path> [options]\n";
        return 1;
    }
    
    // Parse command line arguments
    for ($i = 2; $i < count($argv); $i++) {
        switch ($argv[$i]) {
            case '--paths':
            case '-p':
                $paths = [];
                $i++;
                while ($i < count($argv) && !str_starts_with($argv[$i], '-')) {
                    $paths[] = $argv[$i];
                    $i++;
                }
                $i--; // Adjust for the outer loop increment
                break;
                
            case '--level':
            case '-l':
                $level = (int)$argv[++$i];
                break;
                
            case '--config':
            case '-c':
                $configPath = $argv[++$i];
                break;
                
            case '--max-errors':
            case '-m':
                $maxErrors = (int)$argv[++$i];
                break;
                
            case '--max-iterations':
            case '-i':
                $maxIterations = (int)$argv[++$i];
                break;
                
            case '--verbose':
            case '-v':
                $verbose = true;
                break;
                
            case '--stats-file':
                $statsFile = $argv[++$i];
                break;
        }
    }
    
    // Initialize incremental processor
    $processor = new IncrementalProcessor(
        $projectPath,
        $maxErrors,
        $maxIterations,
        null,
        $verbose
    );
    
    // Process PHPStan errors
    $success = $processor->process($paths, $level, $configPath);
    
    // Save statistics if requested
    if ($statsFile) {
        $stats = $processor->getStats();
        file_put_contents($statsFile, json_encode($stats, JSON_PRETTY_PRINT));
    }
    
    return $success ? 0 : 1;
}

// Only run main when script is executed directly
if (isset($argv[0]) && basename($argv[0]) === basename(__FILE__)) {
    exit(main($argv));
}
