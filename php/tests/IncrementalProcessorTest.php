<?php

namespace MCP\PHPStan\Tests;

use PHPUnit\Framework\TestCase;
use MCP\PHPStan\IncrementalProcessor;

/**
 * Test case for IncrementalProcessor
 */
class IncrementalProcessorTest extends TestCase
{
    /**
     * Test the incremental processor
     */
    public function testIncrementalProcessor(): void
    {
        // Path to the sample PHP project
        $projectPath = realpath(__DIR__ . '/../..') . '/samples/php_project';
        
        // Create a test processor
        $processor = new IncrementalProcessor(
            $projectPath,
            2,  // max_errors_per_batch
            2,  // max_iterations
            null, // phpstan_binary
            true // verbose
        );
        
        // Run a test process (dry run)
        echo "Testing incremental processor...\n";
        
        // We'll mock the process method to avoid actual execution
        // In a real test, you might want to use a mock for the McpClient
        $this->assertInstanceOf(IncrementalProcessor::class, $processor);
        
        // Test the stats method
        $stats = $processor->getStats();
        $this->assertIsArray($stats);
        $this->assertArrayHasKey('iterations', $stats);
        $this->assertArrayHasKey('total_errors_fixed', $stats);
        $this->assertArrayHasKey('total_batches_processed', $stats);
        $this->assertArrayHasKey('errors_by_type', $stats);
        
        echo "\nProcessor stats:\n";
        echo json_encode($stats, JSON_PRETTY_PRINT) . "\n";
    }
    
    /**
     * Test the processor with mock data
     */
    public function testProcessorWithMockData(): void
    {
        // Create a mock processor using a test double
        $mockProcessor = $this->getMockBuilder(IncrementalProcessor::class)
            ->setConstructorArgs([
                '/tmp/mock_project',
                2,  // max_errors_per_batch
                2,  // max_iterations
                null, // phpstan_binary
                false // verbose
            ])
            ->onlyMethods(['process'])
            ->getMock();
        
        // Configure the mock to return true (all errors fixed)
        $mockProcessor->method('process')
            ->willReturn(true);
        
        // Test the mock
        $result = $mockProcessor->process();
        $this->assertTrue($result);
        
        // Test stats after processing
        $stats = $mockProcessor->getStats();
        $this->assertIsArray($stats);
    }
}
