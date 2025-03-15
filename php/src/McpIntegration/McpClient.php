<?php

namespace MCP\PHPStan\McpIntegration;

use MCP\PHPStan\PhpStanRunner\PhpStanRunner;
use MCP\PHPStan\ErrorFormatter\PhpStanErrorFormatter;
use MCP\PHPStan\McpIntegration\ClaudeApiClient;

/**
 * MCP (Multi-agent Conversation Protocol) Client for PHPStan Integration
 *
 * This class provides functionality to integrate PHPStan with Claude Code via MCP.
 * It handles sending PHPStan errors to Claude and processing the responses.
 */
class McpClient
{
    private string $projectPath;
    private int $maxErrorsPerBatch;
    private PhpStanRunner $phpstanRunner;
    private PhpStanErrorFormatter $errorFormatter;

    /**
     * Initialize the MCP client
     *
     * @param string $projectPath Path to the PHP project
     * @param int $maxErrorsPerBatch Maximum number of errors to process in a single batch
     * @param string|null $phpstanBinary Path to the PHPStan binary
     */
    public function __construct(
        string $projectPath,
        int $maxErrorsPerBatch = 3,
        ?string $phpstanBinary = null
    ) {
        $this->projectPath = realpath($projectPath);
        $this->maxErrorsPerBatch = $maxErrorsPerBatch;
        
        // Initialize PHPStan runner
        $this->phpstanRunner = new PhpStanRunner($projectPath, $phpstanBinary);
        
        // Initialize error formatter
        $this->errorFormatter = new PhpStanErrorFormatter($maxErrorsPerBatch);
    }

    /**
     * Run PHPStan analysis and format the errors
     *
     * @param array|null $paths List of paths to analyze
     * @param int|null $level PHPStan rule level (0-9)
     * @param string|null $configPath Path to PHPStan config file
     * @param bool $verbose Whether to run in verbose mode
     * @return array{0: string, 1: int, 2: array} Tuple of (raw_output, return_code, formatted_batches)
     */
    public function runPhpstanAnalysis(
        ?array $paths = null,
        ?int $level = null,
        ?string $configPath = null,
        bool $verbose = false
    ): array {
        // Run PHPStan analysis
        list($output, $returnCode) = $this->phpstanRunner->runAnalysis($paths, $level, $configPath, $verbose);
        
        // If analysis failed or no errors found, return early
        if ($returnCode === 0) {
            return [$output, $returnCode, []];
        }
        
        // Parse the errors
        $errors = $this->errorFormatter->parsePhpstanOutput($output);
        
        // Calculate total batches
        $totalBatches = $this->errorFormatter->getTotalBatches(count($errors));
        
        // Format errors into batches
        $batches = [];
        for ($batchIdx = 0; $batchIdx < $totalBatches; $batchIdx++) {
            $formatted = $this->errorFormatter->formatForMcp($errors, $batchIdx);
            $batches[] = $formatted;
        }
        
        return [$output, $returnCode, $batches];
    }

    /**
     * Prepare a message for Claude Code via MCP
     *
     * @param array $batch Formatted batch of errors
     * @param array|null $fileContents Dictionary mapping file paths to their contents
     * @return array MCP message dictionary
     */
    public function prepareMcpMessage(array $batch, ?array $fileContents = null): array
    {
        // If file_contents not provided, read the files
        if ($fileContents === null) {
            $fileContents = [];
            foreach (array_keys($batch['errors_by_file']) as $filePath) {
                $fullPath = $this->projectPath . '/' . $filePath;
                if (file_exists($fullPath)) {
                    $fileContents[$filePath] = file_get_contents($fullPath);
                }
            }
        }
        
        // Prepare the MCP message
        $message = [
            'type' => 'mcp_phpstan_errors',
            'batch_info' => $batch['batch'],
            'errors' => $batch['errors_by_file'],
            'file_contents' => $fileContents,
            'project_path' => $this->projectPath
        ];
        
        return $message;
    }

    /**
     * Send a message to Claude Code via MCP
     *
     * This method integrates with the Claude API to send error information
     * and receive suggested fixes.
     *
     * @param array $message MCP message to send
     * @return array Claude's response
     */
    public function sendToClaude(array $message): array
    {
        echo "Sending message to Claude Code via MCP:\n";
        echo json_encode($message, JSON_PRETTY_PRINT) . "\n";
        
        // Get API key from environment
        $apiKey = getenv('CLAUDE_API_KEY');
        
        if (!$apiKey) {
            return [
                'status' => 'error',
                'message' => 'Claude API key not found in environment variables',
                'fixes' => []
            ];
        }
        
        try {
            // Initialize Claude API client
            $claudeClient = new ClaudeApiClient($apiKey);
            
            // Format the message for Claude
            $formattedMessage = [
                'type' => 'phpstan_errors',
                'request' => 'Please analyze these PHPStan errors and suggest fixes',
                'data' => $message
            ];
            
            // Send to Claude API
            $response = $claudeClient->sendMessage($formattedMessage);
            
            // Extract fixes from Claude's response
            $fixes = $claudeClient->extractFixes($response);
            
            return [
                'status' => 'success',
                'message' => $response['content'][0]['text'] ?? 'No response text',
                'fixes' => $fixes
            ];
        } catch (\Exception $e) {
            return [
                'status' => 'error',
                'message' => 'Error communicating with Claude: ' . $e->getMessage(),
                'fixes' => []
            ];
        }
    }

    /**
     * Apply fixes suggested by Claude
     *
     * This method applies the fixes suggested by Claude to the PHP files.
     *
     * @param array $fixes List of fixes to apply
     * @return bool True if all fixes were applied successfully, False otherwise
     */
    public function applyFixes(array $fixes): bool
    {
        echo "Applying fixes suggested by Claude:\n";
        echo json_encode($fixes, JSON_PRETTY_PRINT) . "\n";
        
        $success = true;
        
        foreach ($fixes as $fix) {
            $filePath = $this->projectPath . '/' . $fix['file'];
            
            if (!file_exists($filePath)) {
                echo "Error: File {$fix['file']} not found\n";
                $success = false;
                continue;
            }
            
            try {
                // Read the file content
                $content = file_get_contents($filePath);
                
                // Get the line to replace
                $lines = explode("\n", $content);
                $lineIndex = $fix['line'] - 1;
                
                if (!isset($lines[$lineIndex])) {
                    echo "Error: Line {$fix['line']} not found in {$fix['file']}\n";
                    $success = false;
                    continue;
                }
                
                // Replace the line
                $lines[$lineIndex] = $fix['fixed'];
                
                // Write the updated content back to the file
                file_put_contents($filePath, implode("\n", $lines));
                
                echo "Fixed {$fix['file']} line {$fix['line']}\n";
            } catch (\Exception $e) {
                echo "Error applying fix to {$fix['file']}: {$e->getMessage()}\n";
                $success = false;
            }
        }
        
        return $success;
    }

    /**
     * Process PHPStan errors with Claude Code via MCP
     *
     * This method runs PHPStan, sends the errors to Claude, applies the fixes,
     * and repeats until all errors are fixed or max_iterations is reached.
     *
     * @param array|null $paths List of paths to analyze
     * @param int|null $level PHPStan rule level (0-9)
     * @param string|null $configPath Path to PHPStan config file
     * @param bool $verbose Whether to run in verbose mode
     * @param int $maxIterations Maximum number of iterations to run
     * @return bool True if all errors were fixed, False otherwise
     */
    public function processPhpstanErrors(
        ?array $paths = null,
        ?int $level = null,
        ?string $configPath = null,
        bool $verbose = false,
        int $maxIterations = 10
    ): bool {
        $iteration = 0;
        
        while ($iteration < $maxIterations) {
            echo "\nIteration " . ($iteration + 1) . "/$maxIterations\n";
            
            // Run PHPStan analysis
            list($output, $returnCode, $batches) = $this->runPhpstanAnalysis($paths, $level, $configPath, $verbose);
            
            // If no errors, we're done
            if ($returnCode === 0) {
                echo "No PHPStan errors found. All fixed!\n";
                return true;
            }
            
            // If there are errors, process them in batches
            echo "Found " . count($batches) . " batches of errors\n";
            
            foreach ($batches as $batchIdx => $batch) {
                echo "\nProcessing batch " . ($batchIdx + 1) . "/" . count($batches) . "\n";
                
                // Prepare MCP message
                $message = $this->prepareMcpMessage($batch);
                
                // Send to Claude
                $response = $this->sendToClaude($message);
                
                // Apply fixes
                if (isset($response['fixes']) && !empty($response['fixes'])) {
                    $success = $this->applyFixes($response['fixes']);
                    if (!$success) {
                        echo "Failed to apply fixes\n";
                        return false;
                    }
                } else {
                    echo "No fixes suggested by Claude\n";
                }
            }
            
            // Increment iteration counter
            $iteration++;
        }
        
        // If we've reached max_iterations, we've failed to fix all errors
        echo "Reached maximum iterations ($maxIterations) without fixing all errors\n";
        return false;
    }
}

/**
 * Main entry point for the MCP client
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
    $verbose = false;
    $maxErrors = 3;
    $maxIterations = 10;
    
    // Check if project path is provided
    if (!$projectPath) {
        echo "Error: Project path is required\n";
        echo "Usage: php McpClient.php <project_path> [options]\n";
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
                
            case '--verbose':
            case '-v':
                $verbose = true;
                break;
                
            case '--max-errors':
            case '-m':
                $maxErrors = (int)$argv[++$i];
                break;
                
            case '--max-iterations':
            case '-i':
                $maxIterations = (int)$argv[++$i];
                break;
        }
    }
    
    // Initialize MCP client
    $client = new McpClient($projectPath, $maxErrors);
    
    // Process PHPStan errors
    $success = $client->processPhpstanErrors(
        $paths,
        $level,
        $configPath,
        $verbose,
        $maxIterations
    );
    
    // Return appropriate exit code
    return $success ? 0 : 1;
}

// Only run main when script is executed directly
if (isset($argv[0]) && basename($argv[0]) === basename(__FILE__)) {
    exit(main($argv));
}
