# AvalAgent

A Python client for interacting with AI models via the AvalAI OpenAI-compatible API, featuring automatic retries, model fallback, and robust error handling.

## Features

- 🚀 **Multi-model support**: Works with GPT-4o, DeepSeek, Claude-3, and other AvalAI-supported models.
- 🔄 **Automatic retries & fallback**: Falls back to secondary models if the primary model fails.
- 🔒 **Secure API key handling**: Uses `SecretStr` for API key protection to ensure sensitive information is not exposed.
- 📝 **Built-in logging**: Detailed logging for debugging and monitoring API requests.
- ⚡ **LangChain integration**: Compatible with LangChain's message formats for seamless integration.

## Installation

To install AvalAgent, simply run:

```bash
pip install avalAgent
```
### Basic Usage
- Here's how to use the AvalAgent class to interact with the API.

```python  
from avalAgent.agent import AvalAgent
from pydantic import SecretStr

# Initialize with your AvalAI API key
agent = AvalAgent(api_key=SecretStr("your-api-key-here"))

# Get a response
response = agent.get_response(
    system_prompt="You are a helpful assistant.",
    query="Explain quantum computing in simple terms"
)

print(response)
```
### Example 1: Using Default Settings
- This example uses the default settings with automatic retries and model fallback.
```python
from avalAgent.agent import AvalAgent
from pydantic import SecretStr

# Initialize with your AvalAI API key
agent = AvalAgent(api_key=SecretStr("your-api-key-here"))

# Get a response
response = agent.get_response(
    system_prompt="You are a helpful assistant.",
    query="Explain the theory of relativity"
)

print(response)
```
### Example 2: Customizing Model Priority List and Retry Attempts
- You can specify the list of models to be used and the number of retry attempts.
```python
from avalAgent.agent import AvalAgent
from pydantic import SecretStr

# Custom settings: Define model priority and retry attempts
agent = AvalAgent(
    api_key=SecretStr("your-api-key-here"),
    model_priority_list=[
        "gpt-4o",            # First choice
        "deepseek-chat",      # Second choice
        "anthropic.claude-3-5-sonnet-20241022-v2:0"  # Fallback model
    ],
    stop_after_attempt=5  # Retry up to 5 times
)

# Get a response with a specific model
response = agent.get_response(
    system_prompt="You are a technical expert.",
    query="Explain how blockchain works.",
    model="gpt-4o",  # Optional override to use specific model
    temperature=0.2   # Adjust creativity
)

print(response)
```
### Example 3: Fetching User Credit Information
- In this example, you can use the get_credit_info method to fetch and log your credit information in a formatted table.
```python
from avalAgent.agent import AvalAgent
from pydantic import SecretStr

# Initialize with your AvalAI API key
agent = AvalAgent(api_key=SecretStr("your-api-key-here"))

# Fetch and log the user's credit info
agent.get_credit_info()  # Logs credit information in a nice table format
```
# Model Support
- OpenAI-compatible models available through the [AvalAI](https://avalai.ir/) API.

# Error Handling
- The agent automatically:

  - Retries failed requests (up to 3 times by default).

  - Falls back to secondary models if the primary model fails.

  - Handles rate limits and network errors gracefully, with detailed logging for debugging.

# License
 - This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.