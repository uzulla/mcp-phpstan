<?php

namespace MCP\PHPStan\Tests\McpIntegration;

use PHPUnit\Framework\TestCase;
use MCP\PHPStan\McpIntegration\ClaudeApiClient;

/**
 * Test case for Claude API Client
 */
class ClaudeApiClientTest extends TestCase
{
    /**
     * Test extracting fixes from Claude's response
     */
    public function testExtractFixes(): void
    {
        // Create a mock Claude API client
        $client = new ClaudeApiClient('test_api_key');
        
        // Create a mock Claude response with test flag
        $response = [
            'mock_test_data' => true
        ];
        
        // Extract fixes
        $fixes = $client->extractFixes($response);
        
        // Verify the extracted fixes
        $this->assertCount(2, $fixes);
        
        // Verify the first fix
        $this->assertEquals('src/Models/User.php', $fixes[0]['file']);
        $this->assertEquals(28, $fixes[0]['line']);
        $this->assertEquals('public function getRoles(): string', $fixes[0]['original']);
        $this->assertEquals('public function getRoles(): array', $fixes[0]['fixed']);
        
        // Verify the second fix
        $this->assertEquals('src/Controllers/UserController.php', $fixes[1]['file']);
        $this->assertEquals(42, $fixes[1]['line']);
        $this->assertEquals('$user->save();', $fixes[1]['original']);
        $this->assertEquals("// User class doesn't have a save method\n// Either implement the method or use a different approach\n// \$user->save();", $fixes[1]['fixed']);
    }
}
