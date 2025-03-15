<?php

namespace MCP\PHPStan\PhpStanRunner;

/**
 * PHPStan Runner Module
 *
 * This class provides functionality to run PHPStan on PHP projects and capture the output.
 */
class PhpStanRunner
{
    private string $projectPath;
    private string $phpstanBinary;

    /**
     * Initialize the PHPStan runner
     *
     * @param string $projectPath Path to the PHP project
     * @param string|null $phpstanBinary Path to the PHPStan binary (defaults to vendor/bin/phpstan)
     * @throws \InvalidArgumentException If project path does not exist
     */
    public function __construct(string $projectPath, ?string $phpstanBinary = null)
    {
        $this->projectPath = realpath($projectPath);
        
        if ($phpstanBinary) {
            $this->phpstanBinary = $phpstanBinary;
        } else {
            // Default PHPStan binary path
            $this->phpstanBinary = $this->projectPath . '/vendor/bin/phpstan';
        }
        
        // Check if the project path exists
        if (!is_dir($this->projectPath)) {
            throw new \InvalidArgumentException("Project path does not exist: {$this->projectPath}");
        }
    }

    /**
     * Run PHPStan analysis on the project
     *
     * @param array|null $paths List of paths to analyze (defaults to paths in config)
     * @param int|null $level PHPStan rule level (0-9, defaults to level in config)
     * @param string|null $configPath Path to PHPStan config file (defaults to phpstan.neon in project root)
     * @param bool $verbose Whether to run in verbose mode
     * @return array{0: string, 1: int} Tuple of (output, return_code)
     */
    public function runAnalysis(?array $paths = null, ?int $level = null, ?string $configPath = null, bool $verbose = false): array
    {
        // Build the command
        $cmd = [$this->phpstanBinary, 'analyse'];
        
        // Add verbose flag if requested
        if ($verbose) {
            $cmd[] = '-v';
        }
        
        // Add level if specified
        if ($level !== null) {
            $cmd[] = '--level';
            $cmd[] = (string)$level;
        }
        
        // Add config path if specified
        if ($configPath) {
            $cmd[] = '--configuration';
            $cmd[] = $configPath;
        }
        
        // Add paths to analyze if specified
        if ($paths) {
            $cmd = array_merge($cmd, $paths);
        }
        
        // Run the command
        try {
            $process = proc_open(
                implode(' ', array_map('escapeshellarg', $cmd)),
                [
                    1 => ['pipe', 'w'],
                    2 => ['pipe', 'w'],
                ],
                $pipes,
                $this->projectPath
            );
            
            if (is_resource($process)) {
                $stdout = stream_get_contents($pipes[1]);
                $stderr = stream_get_contents($pipes[2]);
                fclose($pipes[1]);
                fclose($pipes[2]);
                $returnCode = proc_close($process);
                
                return [$stdout . $stderr, $returnCode];
            }
            
            return ["Failed to execute PHPStan command", 1];
        } catch (\Exception $e) {
            return ["Error running PHPStan: {$e->getMessage()}", 1];
        }
    }

    /**
     * Check if PHPStan is properly installed
     *
     * @return bool True if PHPStan is installed, False otherwise
     */
    public function checkInstallation(): bool
    {
        if (!file_exists($this->phpstanBinary)) {
            return false;
        }
            
        try {
            $process = proc_open(
                escapeshellarg($this->phpstanBinary) . ' --version',
                [
                    1 => ['pipe', 'w'],
                    2 => ['pipe', 'w'],
                ],
                $pipes,
                $this->projectPath
            );
            
            if (is_resource($process)) {
                fclose($pipes[1]);
                fclose($pipes[2]);
                $returnCode = proc_close($process);
                
                return $returnCode === 0;
            }
            
            return false;
        } catch (\Exception $e) {
            return false;
        }
    }
}
