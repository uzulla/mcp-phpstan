# Setting Up Claude Code with MCP for PHPStan Integration

This guide explains how to set up Claude Code with Model Context Protocol (MCP) to work with the PHPStan Integration tool.

## Prerequisites

- Access to Claude Code (Anthropic's Claude API)
- Understanding of MCP (Model Context Protocol)
- The MCP PHPStan Integration tool installed

## What is MCP?

MCP (Model Context Protocol) is a protocol that allows LLMs like Claude to interact with external tools and services. In this case, we're using it to enable Claude to:

1. Receive PHPStan errors from your PHP code
2. Analyze the errors and suggest fixes
3. Return the fixes in a structured format that our tool can apply

## Setting Up Claude Code with MCP

### 1. Obtain Claude API Access

To use Claude Code with MCP, you need access to the Claude API. Visit [Anthropic's website](https://www.anthropic.com/) to sign up for API access if you don't already have it.

### 2. Configure Claude for MCP

Claude needs to be configured to understand the MCP protocol and specifically the PHPStan integration. This typically involves:

- Setting up the appropriate model (Claude 3 Opus or later recommended)
- Configuring the model to understand the MCP protocol
- Setting up the appropriate tools and permissions

For detailed instructions, refer to Anthropic's documentation on setting up Claude with MCP.

### 3. Configure the MCP PHPStan Integration Tool

Once you have Claude set up with MCP, you need to configure the MCP PHPStan Integration tool to communicate with your Claude instance:

1. Open `src/McpIntegration/McpClient.py`
2. Locate the `send_to_claude()` method
3. Replace the placeholder implementation with code that communicates with your Claude instance via the API
4. Add your Claude API key (securely, e.g., using environment variables)

Example implementation:

```python
def send_to_claude(self, message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a message to Claude Code via MCP.
    
    Args:
        message: MCP message to send
        
    Returns:
        Claude's response
    """
    import requests
    import os
    
    # Get API key from environment variable
    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        raise ValueError("CLAUDE_API_KEY environment variable not set")
    
    # Prepare the request
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    
    # Convert the message to the format expected by Claude
    claude_message = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 4000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please analyze these PHPStan errors and suggest fixes:"
                    },
                    {
                        "type": "mcp_phpstan_errors",
                        "mcp_phpstan_errors": message
                    }
                ]
            }
        ]
    }
    
    # Send the request to Claude
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=claude_message
    )
    
    # Parse the response
    if response.status_code == 200:
        claude_response = response.json()
        
        # Extract the fixes from Claude's response
        # This will depend on the exact format of Claude's response
        # You may need to adjust this based on your specific implementation
        fixes = []
        for content in claude_response["content"]:
            if content["type"] == "mcp_phpstan_fixes":
                fixes = content["mcp_phpstan_fixes"]
        
        return {
            "status": "success",
            "message": claude_response["text"],
            "fixes": fixes
        }
    else:
        return {
            "status": "error",
            "message": f"Error communicating with Claude: {response.status_code} {response.text}",
            "fixes": []
        }
```

### 4. Set Up Environment Variables

Set up the necessary environment variables:

```bash
export CLAUDE_API_KEY=your_api_key_here
```

For production use, consider using a more secure method of storing and accessing your API key.

## Testing the Integration

After setting up Claude with MCP, you should test the integration:

1. Run the tool in dry-run mode:
   ```bash
   python3 src/main.py /path/to/your/php/project --dry-run
   ```

2. Check the output to ensure that:
   - PHPStan errors are detected correctly
   - The errors are formatted correctly for MCP
   - The formatted errors are sent to Claude
   - Claude's response is received and parsed correctly

3. If everything looks good, run the tool without the dry-run flag to apply the fixes:
   ```bash
   python3 src/main.py /path/to/your/php/project
   ```

## Troubleshooting

### Claude Not Receiving Errors

If Claude is not receiving the errors:
- Check that your API key is correct
- Verify that the message format matches what Claude expects
- Check for any network issues or API rate limits

### Claude Not Suggesting Fixes

If Claude is receiving the errors but not suggesting fixes:
- Check that Claude is configured to understand the MCP protocol
- Verify that the message format includes all necessary information
- Try reducing the batch size to simplify the task for Claude

### Fixes Not Being Applied

If Claude is suggesting fixes but they're not being applied:
- Check the format of Claude's response
- Verify that the `apply_fixes()` method is correctly parsing the response
- Check for any errors in the application of the fixes

## Advanced Configuration

### Customizing the Message Format

You can customize the message format sent to Claude by modifying the `prepare_mcp_message()` method in `src/McpIntegration/McpClient.py`.

### Customizing the Response Parsing

You can customize how Claude's responses are parsed by modifying the `send_to_claude()` method in `src/McpIntegration/McpClient.py`.

### Customizing the Fix Application

You can customize how fixes are applied by modifying the `apply_fixes()` method in `src/McpIntegration/McpClient.py`.

## Further Resources

- [Anthropic's Claude API Documentation](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [MCP Documentation](https://github.com/auchenberg/claude-code-mcp)
- [PHPStan Documentation](https://phpstan.org/user-guide/getting-started)
