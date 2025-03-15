<?php

namespace MCP\PHPStan\Tests\ErrorFormatter;

use PHPUnit\Framework\TestCase;
use MCP\PHPStan\ErrorFormatter\PhpStanErrorFormatter;
use function MCP\PHPStan\ErrorFormatter\formatPhpstanOutput;

/**
 * Test case for PHPStan error formatter
 */
class FormatterTest extends TestCase
{
    /**
     * Test the formatter with sample PHPStan output
     */
    public function testFormatPhpstanOutput(): void
    {
        // Path to the sample PHP project
        $projectPath = realpath(__DIR__ . '/../../..') . '/samples/php_project';
        
        // Run PHPStan analysis using the function from Runner.php
        echo "Running PHPStan analysis...\n";
        list($phpstanOutput, $returnCode) = \MCP\PHPStan\PhpStanRunner\runPhpstan($projectPath, null, null, null, null, true);
        
        if ($returnCode !== 0) {
            echo "PHPStan analysis completed with {$returnCode} errors.\n";
        } else {
            echo "PHPStan analysis completed successfully (no errors).\n";
        }
        
        // Format the output for different batch sizes
        echo "\nFormatting errors (batch size: 3, batch index: 0):\n";
        $formattedOutput = formatPhpstanOutput($phpstanOutput, 3, 0);
        echo $formattedOutput . "\n";
        
        // Parse the formatted output to check batch information
        $parsed = json_decode($formattedOutput, true);
        
        // Verify the structure of the formatted output
        $this->assertArrayHasKey('batch', $parsed);
        $this->assertArrayHasKey('errors_by_file', $parsed);
        $this->assertArrayHasKey('index', $parsed['batch']);
        $this->assertArrayHasKey('total_errors', $parsed['batch']);
        $this->assertArrayHasKey('batch_size', $parsed['batch']);
        $this->assertArrayHasKey('has_more', $parsed['batch']);
        
        $totalErrors = $parsed['batch']['total_errors'];
        
        // Test the second batch if there are more errors
        if ($parsed['batch']['has_more']) {
            echo "\nFormatting errors (batch size: 3, batch index: 1):\n";
            $formattedOutput = formatPhpstanOutput($phpstanOutput, 3, 1);
            echo $formattedOutput . "\n";
            
            $parsed = json_decode($formattedOutput, true);
            $this->assertArrayHasKey('batch', $parsed);
            $this->assertArrayHasKey('errors_by_file', $parsed);
            $this->assertEquals(1, $parsed['batch']['index']);
        }
    }
    
    /**
     * Test the formatter with a mock PHPStan output
     */
    public function testFormatterWithMockOutput(): void
    {
        // Create a mock PHPStan output
        $mockOutput = <<<EOT
 ------ -------------------------------------------------------------------------------------- 
  Line   src/Models/User.php                                                                  
 ------ -------------------------------------------------------------------------------------- 
  15     Property User::\$email type has no value type specified in iterable type array.      
         🪪 PHPStan\Rules\Properties\MissingPropertyType                                      
         💡 Add array<string> type to property User::\$email                                  
  28     Method User::validateEmail() has parameter \$email with no type specified.           
         🪪 PHPStan\Rules\Methods\MissingParameterType                                        
 ------ -------------------------------------------------------------------------------------- 
  Line   src/Controllers/UserController.php                                                   
 ------ -------------------------------------------------------------------------------------- 
  42     Call to method save() on an unknown class User.                                      
         🪪 PHPStan\Rules\Methods\CallToNonExistentMethod                                     
EOT;

        // Format the mock output
        $formatter = new PhpStanErrorFormatter(2);
        $errors = $formatter->parsePhpstanOutput($mockOutput);
        
        // Verify the parsed errors
        $this->assertCount(3, $errors);
        
        // Verify the first error
        $this->assertEquals('Property User::$email type has no value type specified in iterable type array.', $errors[0]->toArray()['message']);
        $this->assertEquals('src/Models/User.php', $errors[0]->toArray()['file']);
        $this->assertEquals(15, $errors[0]->toArray()['line']);
        $this->assertEquals('type_error', $errors[0]->toArray()['error_type']);
        
        // Format for MCP and verify the structure
        $formatted = $formatter->formatForMcp($errors, 0);
        $this->assertArrayHasKey('batch', $formatted);
        $this->assertArrayHasKey('errors_by_file', $formatted);
        $this->assertEquals(0, $formatted['batch']['index']);
        $this->assertEquals(3, $formatted['batch']['total_errors']);
        $this->assertEquals(2, $formatted['batch']['batch_size']);
        $this->assertTrue($formatted['batch']['has_more']);
        
        // Test the second batch
        $formatted = $formatter->formatForMcp($errors, 1);
        $this->assertArrayHasKey('batch', $formatted);
        $this->assertArrayHasKey('errors_by_file', $formatted);
        $this->assertEquals(1, $formatted['batch']['index']);
        $this->assertEquals(3, $formatted['batch']['total_errors']);
        $this->assertEquals(1, $formatted['batch']['batch_size']);
        $this->assertFalse($formatted['batch']['has_more']);
    }
}
