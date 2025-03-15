<?php

namespace MCP\PHPStan\ErrorFormatter;

/**
 * Format PHPStan output for MCP
 *
 * @param string $phpstanOutput Raw PHPStan output
 * @param int $maxErrorsPerBatch Maximum errors per batch
 * @param int $batchIndex Current batch index
 * @return string JSON string formatted for MCP
 */
function formatPhpstanOutput(string $phpstanOutput, int $maxErrorsPerBatch = 5, int $batchIndex = 0): string
{
    $formatter = new PhpStanErrorFormatter($maxErrorsPerBatch);
    $errors = $formatter->parsePhpstanOutput($phpstanOutput);
    $formatted = $formatter->formatForMcp($errors, $batchIndex);
    return json_encode($formatted, JSON_PRETTY_PRINT);
}
