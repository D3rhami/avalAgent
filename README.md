# AvalAgent 1.0.3

A Python client for interacting with AI models via the AvalAI OpenAI-compatible API, featuring automatic retries, model fallback, conversation memory, and robust error handling.

## Features

- 🚀 **Multi-model support**: Works with GPT-4o, DeepSeek, Claude-3, and other AvalAI-supported models
- 🔄 **Automatic retries & fallback**: Falls back to secondary models if the primary model fails
- 🧠 **Conversation memory**: Maintains context across interactions (configurable size)
- 💾 **Memory persistence**: Optional saving/loading of conversation history to disk
- 🔒 **Secure API key handling**: Uses `SecretStr` for API key protection
- 📝 **Built-in logging**: Detailed logging for debugging and monitoring API requests
- ⚡ **LangChain integration**: Compatible with LangChain's message formats
- 📊 **Credit monitoring**: Check API usage and remaining credits

## Installation

```bash
pip install avalAgent
```

## Basic Usage

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

## Examples

### Example 1: Using Default Settings

```python
from avalAgent.agent import AvalAgent
from pydantic import SecretStr

agent = AvalAgent(api_key=SecretStr("your-api-key-here"))

response = agent.get_response(
    system_prompt="You are a helpful assistant.",
    query="Explain the theory of relativity"
)

print(response)
```

### Example 2: Customizing Model Priority List and Retry Attempts

```python
from avalAgent.agent import AvalAgent
from pydantic import SecretStr

agent = AvalAgent(
    api_key=SecretStr("your-api-key-here"),
    model_priority_list=[
        "gpt-4o",
        "deepseek-chat",
        "anthropic.claude-3-5-sonnet-20241022-v2:0"
    ],
    stop_after_attempt=5
)

response = agent.get_response(
    system_prompt="You are a technical expert.",
    query="Explain how blockchain works.",
    model="gpt-4o",
    temperature=0.2
)

print(response)
```

### Example 3: Using Conversation Memory

```python
from avalAgent.agent import AvalAgent
from pydantic import SecretStr

# Initialize with memory enabled
agent = AvalAgent(
    api_key=SecretStr("your-api-key-here"),
    use_memory=True,
    max_memory_size=5
)

# First query establishes context
response1 = agent.get_response(
    system_prompt="You are a travel assistant.",
    query="Tell me about tourist attractions in Paris"
)

# Second query benefits from memory
response2 = agent.get_response(
    query="Which of these are good for children?"
)

print(response2)
```

### Example 4: Persistent Memory Across Sessions

```python
from avalAgent.agent import AvalAgent
from pydantic import SecretStr

# First session - save memory
agent1 = AvalAgent(
    api_key=SecretStr("your-api-key-here"),
    use_memory=True,
    persist_memory=True,
    memory_file="travel_chat.json"
)

response = agent1.get_response(
    system_prompt="You are a travel assistant.",
    query="What are the best museums in London?"
)

# Second session - load previous memory
agent2 = AvalAgent(
    api_key=SecretStr("your-api-key-here"),
    use_memory=True,
    persist_memory=True,
    memory_file="travel_chat.json"
)

# Continues previous conversation
response = agent2.get_response(
    query="Which of these have free entry?"
)

print(response)
```

### Example 5: Credit Information Monitoring

```python
from avalAgent.agent import AvalAgent
from pydantic import SecretStr

agent = AvalAgent(api_key=SecretStr("your-api-key-here"))

# Option 1: Just get the data
credit_data = agent.get_credit_info()

# Option 2: Log formatted table
agent.log_credit_info_table()
```

## Update: Version 1.0.3

### New Features
- **Conversation Memory**: Now supports maintaining context across multiple interactions
- **Memory Persistence**: Optional saving/loading of conversation history to/from JSON files
- **Enhanced Credit Monitoring**: Separate methods for getting data and logging formatted tables

### Improvements
- Added memory-related parameters to constructor:
  - `use_memory`: Enable/disable conversation memory
  - `max_memory_size`: Control how many messages to retain
  - `persist_memory`: Enable disk persistence
  - `memory_file`: Customize save location
- New memory management methods:
  - `add_to_memory()`: Manually add messages
  - `get_memory()`: Retrieve conversation history
  - `clear_memory()`: Reset conversation
  - `save_memory()`/`load_memory()`: Disk persistence

### Changes
- Split `get_credit_info()` into:
  - `get_credit_info()`: Returns raw data
  - `log_credit_info_table()`: Displays formatted table
- Memory is automatically used in `get_response()` when enabled

## Model Support

OpenAI-compatible models available through the [AvalAI](https://avalai.ir/) API.

## Error Handling

The agent automatically:
- Retries failed requests (up to 3 times by default)
- Falls back to secondary models if the primary model fails
- Handles rate limits and network errors gracefully
- Provides detailed logging for debugging

## License

MIT License - see the [LICENSE](LICENSE) file for details.
