<?php

namespace MCP\PHPStan\ErrorFormatter;

/**
 * PHPStan Error Formatter for MCP
 *
 * This class formats PHPStan errors into a structure suitable for processing by Claude via MCP.
 * It handles parsing the PHPStan output and converting it to a format that can be used with MCP.
 */
class PhpStanError
{
    private string $message;
    private string $file;
    private int $line;
    private string $errorType;
    private ?string $errorCode;
    private ?string $suggestion;

    /**
     * @param string $message Error message
     * @param string $file File path
     * @param int $line Line number
     * @param string $errorType Type of error
     * @param string|null $errorCode Error code from PHPStan
     * @param string|null $suggestion Suggested fix
     */
    public function __construct(
        string $message,
        string $file,
        int $line,
        string $errorType,
        ?string $errorCode = null,
        ?string $suggestion = null
    ) {
        $this->message = $message;
        $this->file = $file;
        $this->line = $line;
        $this->errorType = $errorType;
        $this->errorCode = $errorCode;
        $this->suggestion = $suggestion;
    }

    /**
     * Convert the error to an array representation
     *
     * @return array<string, mixed>
     */
    public function toArray(): array
    {
        $result = [
            'message' => $this->message,
            'file' => $this->file,
            'line' => $this->line,
            'error_type' => $this->errorType,
        ];
        
        if ($this->errorCode) {
            $result['error_code'] = $this->errorCode;
        }
            
        if ($this->suggestion) {
            $result['suggestion'] = $this->suggestion;
        }
            
        return $result;
    }
}

class PhpStanErrorFormatter
{
    private int $maxErrorsPerBatch;

    /**
     * Initialize the formatter
     *
     * @param int $maxErrorsPerBatch Maximum number of errors to include in a single batch
     */
    public function __construct(int $maxErrorsPerBatch = 5)
    {
        $this->maxErrorsPerBatch = $maxErrorsPerBatch;
    }

    /**
     * Parse PHPStan CLI output and extract errors
     *
     * @param string $output The raw output from PHPStan
     * @return array<PhpStanError> List of PhpStanError objects
     */
    public function parsePhpstanOutput(string $output): array
    {
        $errors = [];
        
        // Find file sections in the output
        preg_match_all(
            '/------ +-+ +\n +Line +([^\n]+) +\n +------ +-+ +\n(.*?)(?=\n +------ +-|$)/s',
            $output,
            $fileSections,
            PREG_SET_ORDER
        );
        
        foreach ($fileSections as $fileSection) {
            $fileName = trim($fileSection[1]);
            $sectionContent = $fileSection[2];
            
            // Extract individual errors from each file section
            preg_match_all(
                '/ +(\d+) +([^\n]+)\n +🪪 +([^\n]+)(?:\n +💡 +([^\n]+))?/s',
                $sectionContent,
                $errorMatches,
                PREG_SET_ORDER
            );
            
            foreach ($errorMatches as $match) {
                $lineNum = (int)$match[1];
                $message = trim($match[2]);
                $errorCode = trim($match[3]);
                $suggestion = isset($match[4]) ? trim($match[4]) : null;
                
                // Determine error type from the message or code
                $errorType = $this->determineErrorType($message, $errorCode);
                
                $errors[] = new PhpStanError(
                    $message,
                    $fileName,
                    $lineNum,
                    $errorType,
                    $errorCode,
                    $suggestion
                );
            }
        }
        
        return $errors;
    }

    /**
     * Determine the type of error based on the message and error code
     *
     * @param string $message Error message
     * @param string $errorCode Error code from PHPStan
     * @return string Error type classification
     */
    private function determineErrorType(string $message, string $errorCode): string
    {
        // Check for type-related errors first
        if (stripos($message, 'type has no value type specified') !== false ||
            stripos($message, 'has no typehint specified') !== false ||
            stripos($message, 'has no type specified') !== false) {
            return 'type_error';
        } elseif (stripos($errorCode, 'undefined') !== false) {
            return 'undefined_symbol';
        } elseif (stripos($errorCode, 'missing') !== false) {
            return 'missing_type';
        } elseif (stripos($errorCode, 'not.found') !== false || 
                  stripos($errorCode, 'notFound') !== false) {
            return 'not_found';
        } elseif (stripos($errorCode, 'arguments') !== false) {
            return 'argument_error';
        } elseif (stripos($errorCode, 'type') !== false) {
            return 'type_error';
        } else {
            return 'other';
        }
    }

    /**
     * Format errors for MCP integration
     *
     * @param array<PhpStanError> $errors List of PHPStan errors
     * @param int $batchIndex Index of the current batch when processing incrementally
     * @return array<string, mixed> Dictionary formatted for MCP
     */
    public function formatForMcp(array $errors, int $batchIndex = 0): array
    {
        // Calculate the slice of errors for this batch
        $startIdx = $batchIndex * $this->maxErrorsPerBatch;
        $endIdx = $startIdx + $this->maxErrorsPerBatch;
        $batchErrors = array_slice($errors, $startIdx, $this->maxErrorsPerBatch);
        
        // Group errors by file
        $errorsByFile = [];
        foreach ($batchErrors as $error) {
            if (!isset($errorsByFile[$error->toArray()['file']])) {
                $errorsByFile[$error->toArray()['file']] = [];
            }
            $errorsByFile[$error->toArray()['file']][] = $error->toArray();
        }
        
        // Format for MCP
        return [
            'batch' => [
                'index' => $batchIndex,
                'total_errors' => count($errors),
                'batch_size' => count($batchErrors),
                'has_more' => $endIdx < count($errors)
            ],
            'errors_by_file' => $errorsByFile
        ];
    }

    /**
     * Calculate the total number of batches needed
     *
     * @param int $totalErrors Total number of errors
     * @return int Number of batches needed
     */
    public function getTotalBatches(int $totalErrors): int
    {
        return (int)ceil($totalErrors / $this->maxErrorsPerBatch);
    }
}
