
🎃 [تغییر زبان به فارسی اینجا کلیک کنید](README.md)

# AvalAgent 1.0.4

A Python client for interacting with AI models via the AvalAI OpenAI-compatible API, featuring automatic retries, model fallback, conversation memory, prompt enhancement, and robust error handling.

## Features

- 🚀 **Multi-model support**: Works with GPT-4o, DeepSeek, Claude-3, and other AvalAI-supported models
- 🔄 **Automatic retries & fallback**: Falls back to secondary models if the primary model fails
- 🧠 **Conversation memory**: Maintains context across interactions (configurable size)
- 💾 **Memory persistence**: Optional saving/loading of conversation history to disk
- 🛠️ **Prompt enhancement**: Transforms raw prompts into optimized, structured prompts
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

### Example 5: Prompt Enhancement for Instagram Post

```python
from avalAgent.agent import AvalAgent
from pydantic import SecretStr

agent = AvalAgent(api_key=SecretStr("your-api-key-here"))

raw_prompt = """
I need a Persian Instagram caption for our new collection of luxury handbags.
The caption should:
- Be 2-3 short paragraphs
- Use emojis tastefully
- Highlight the craftsmanship
- Include a call-to-action
- Use friendly but elegant tone
"""

enhanced_prompt = agent.enhance_prompt(raw_prompt)
print(enhanced_prompt)

# Then use the enhanced prompt
response = agent.get_response(
    system_prompt=enhanced_prompt,
    query="Generate 3 caption options"
)
print(response)
```

### Example 6: Credit Information Monitoring

```python
from avalAgent.agent import AvalAgent
from pydantic import SecretStr

agent = AvalAgent(api_key=SecretStr("your-api-key-here"))

# Option 1: Just get the data
credit_data = agent.get_credit_info()

# Option 2: Log formatted table
agent.log_credit_info_table()
```

## Update: Version 1.0.4

### New Features
- **Prompt Enhancement**: New `enhance_prompt()` method to transform raw prompts into structured formats
- **Improved Error Handling**: More robust validation and error messages
- **JSON Configuration**: Support for JSON-based configuration in prompt enhancement

### Improvements
- **API Changes**:
  - `get_response()` now uses `**config` parameters instead of individual args
  - More consistent parameter validation across all methods
- **Memory Management**:
  - Better handling of memory persistence edge cases

### Changes
- **Behavior Changes**:
  - `get_response()` now returns None instead of raising ValueError for empty queries
  - More strict validation in `create_structured_prompt()`
- **Documentation**:
  - Added Persian-language readme
  - More detailed parameter documentation

## Model Support

OpenAI-compatible models available through the Avalai.ir API.
[see the supported models in AvalAI models](https://docs.avalai.ir/fa/models/index).
## Error Handling

The agent automatically:
- Retries failed requests (up to 3 times by default)
- Falls back to secondary models if the primary model fails
- Handles rate limits and network errors gracefully
- Provides detailed logging for debugging

## 🐞 Issues and Support

Found a bug or have a feature request? Please open an issue at [here.](https://github.com/D3rhami/avalai-agent/issues)

## License

MIT License - see the [LICENSE](LICENSE) file for details.
