<?php

namespace App\Utils;

class Logger
{
    private string $logFile;

    public function __construct(string $logFile = 'app.log')
    {
        $this->logFile = $logFile;
    }

    /**
     * @param mixed $message Message to log
     * @return bool Success status
     */
    public function log($message): bool
    {
        // Undefined constant
        if (DEBUG_MODE) {
            echo $message . PHP_EOL;
        }

        // Undefined variable
        return file_put_contents($this->logFile, $message . PHP_EOL, FILE_APPEND);
    }

    // Unused parameter
    public function clearLogs(string $olderThan): void
    {
        // Do nothing
    }
}
