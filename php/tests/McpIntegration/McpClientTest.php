<?php

namespace MCP\PHPStan\Tests\McpIntegration;

use PHPUnit\Framework\TestCase;
use MCP\PHPStan\McpIntegration\McpClient;

/**
 * Test case for MCP integration with PHPStan
 */
class McpClientTest extends TestCase
{
    /**
     * Test the MCP integration with PHPStan
     */
    public function testMcpIntegration(): void
    {
        // Path to the sample PHP project
        $projectPath = realpath(__DIR__ . '/../../..') . '/samples/php_project';
        
        // Initialize MCP client
        $client = new McpClient($projectPath, 3);
        
        // Run PHPStan analysis and get formatted batches
        echo "Running PHPStan analysis...\n";
        list($output, $returnCode, $batches) = $client->runPhpstanAnalysis(null, null, null, true);
        
        if ($returnCode !== 0) {
            echo "PHPStan analysis completed with errors. Found " . count($batches) . " batches.\n";
        } else {
            echo "PHPStan analysis completed successfully (no errors).\n";
            $this->markTestSkipped("No PHPStan errors found, skipping test.");
            return;
        }
        
        // Process the first batch
        if (!empty($batches)) {
            echo "\nPreparing MCP message for first batch:\n";
            $message = $client->prepareMcpMessage($batches[0]);
            
            // Print the message (in a real scenario, this would be sent to Claude)
            echo json_encode($message, JSON_PRETTY_PRINT) . "\n";
            
            // Verify the message structure
            $this->assertArrayHasKey('type', $message);
            $this->assertArrayHasKey('batch_info', $message);
            $this->assertArrayHasKey('errors', $message);
            $this->assertArrayHasKey('file_contents', $message);
            $this->assertArrayHasKey('project_path', $message);
            
            // Simulate sending to Claude
            echo "\nSimulating sending to Claude...\n";
            $response = $client->sendToClaude($message);
            
            echo "\nMock response from Claude:\n";
            echo json_encode($response, JSON_PRETTY_PRINT) . "\n";
            
            // Verify the response structure
            $this->assertArrayHasKey('status', $response);
            $this->assertArrayHasKey('message', $response);
            $this->assertArrayHasKey('fixes', $response);
        } else {
            echo "No error batches found.\n";
            $this->markTestSkipped("No error batches found, skipping test.");
        }
    }
    
    /**
     * Test the MCP client with mock data
     */
    public function testMcpClientWithMockData(): void
    {
        // Create a mock client
        $mockClient = $this->getMockBuilder(McpClient::class)
            ->setConstructorArgs(['/tmp/mock_project', 3])
            ->onlyMethods(['sendToClaude'])
            ->getMock();
        
        // Configure the mock to return a predefined response
        $mockClient->method('sendToClaude')
            ->willReturn([
                'status' => 'success',
                'message' => 'Mock response from Claude',
                'fixes' => [
                    [
                        'file' => 'src/Models/User.php',
                        'line' => 15,
                        'original' => 'private $email = [];',
                        'fixed' => 'private array $email = [];'
                    ]
                ]
            ]);
        
        // Create a mock batch
        $mockBatch = [
            'batch' => [
                'index' => 0,
                'total_errors' => 1,
                'batch_size' => 1,
                'has_more' => false
            ],
            'errors_by_file' => [
                'src/Models/User.php' => [
                    [
                        'message' => 'Property User::$email type has no value type specified in iterable type array.',
                        'file' => 'src/Models/User.php',
                        'line' => 15,
                        'error_type' => 'missing_type'
                    ]
                ]
            ]
        ];
        
        // Prepare message and send to mock Claude
        $message = $mockClient->prepareMcpMessage($mockBatch);
        $response = $mockClient->sendToClaude($message);
        
        // Verify the response
        $this->assertEquals('success', $response['status']);
        $this->assertCount(1, $response['fixes']);
        $this->assertEquals('src/Models/User.php', $response['fixes'][0]['file']);
    }
}
