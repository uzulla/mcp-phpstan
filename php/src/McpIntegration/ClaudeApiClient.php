<?php

namespace MCP\PHPStan\McpIntegration;

use GuzzleHttp\Client;
use GuzzleHttp\Exception\GuzzleException;

/**
 * Claude API Client
 *
 * This class handles communication with the Claude API for code suggestions
 */
class ClaudeApiClient
{
    private Client $httpClient;
    private string $apiKey;
    private string $model;
    
    /**
     * Initialize the Claude API client
     *
     * @param string|null $apiKey API key for Claude (defaults to CLAUDE_API_KEY env var)
     * @param string $model Claude model to use
     */
    public function __construct(?string $apiKey = null, string $model = 'claude-3-opus-20240229')
    {
        $this->apiKey = $apiKey ?? getenv('CLAUDE_API_KEY');
        $this->model = $model;
        
        if (empty($this->apiKey)) {
            throw new \InvalidArgumentException('Claude API key is required. Set CLAUDE_API_KEY environment variable or pass it to the constructor.');
        }
        
        $this->httpClient = new Client([
            'base_uri' => 'https://api.anthropic.com/v1/',
            'headers' => [
                'anthropic-version' => '2023-06-01',
                'x-api-key' => $this->apiKey,
                'Content-Type' => 'application/json'
            ]
        ]);
    }
    
    /**
     * Send a message to Claude API
     *
     * @param array $message Message to send
     * @param int $maxTokens Maximum tokens in the response
     * @return array Claude's response
     * @throws \Exception If there's an error communicating with Claude
     */
    public function sendMessage(array $message, int $maxTokens = 4000): array
    {
        try {
            $response = $this->httpClient->post('messages', [
                'json' => [
                    'model' => $this->model,
                    'max_tokens' => $maxTokens,
                    'messages' => [
                        [
                            'role' => 'user',
                            'content' => json_encode($message)
                        ]
                    ]
                ]
            ]);
            
            return json_decode($response->getBody()->getContents(), true);
        } catch (GuzzleException $e) {
            throw new \Exception('Error communicating with Claude API: ' . $e->getMessage());
        }
    }
    
    /**
     * Extract code fixes from Claude's response
     *
     * @param array $response Claude API response
     * @return array List of fixes
     */
    public function extractFixes(array $response): array
    {
        // In a real implementation, this would parse Claude's response
        // to extract the suggested fixes
        
        // For now, return an empty array
        return [];
    }
}
