from typing import List, Union, Dict, Any
import json
import os
from pathlib import Path

import requests
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from openai import RateLimitError
from pydantic import SecretStr
from tabulate import tabulate

from .logger import get_logger


class AvalAgent:
    """A client for interacting with AI models via an OpenAI-compatible API.

    This class manages API requests to various AI models, handling retries and model fallbacks
    based on a priority list. It supports custom configurations for API key, base URL, and retry attempts.
    """

    def __init__(
            self,
            api_key: SecretStr | str,
            base_url: str = 'https://api.avalai.ir/v1',
            model_priority_list: List[str] = None,
            stop_after_attempt: int = 3,
            use_memory: bool = False,
            max_memory_size: int = 10,
            persist_memory: bool = False,
            memory_file: str = "AvalAgent/agent_memory.json"
    ):
        """Initialize the avalAgent with API credentials and configuration.

        Args:
            api_key (SecretStr): The API key for authentication.
            base_url (str, optional): The base URL of the API. Defaults to 'https://api.avalai.ir/v1'.
            model_priority_list (List[str], optional): A list of model names to try in order.
                Defaults to ["gpt-4o", "gemini-2.5-pro-preview-03-25", "anthropic.claude-3-5-sonnet-20241022-v2:0"].
            stop_after_attempt (int, optional): Maximum number of retry attempts. Defaults to 3.
            use_memory (bool, optional): Whether to use conversation memory. Defaults to False.
            max_memory_size (int, optional): Maximum number of messages to keep in memory. Defaults to 10.
            persist_memory (bool, optional): Whether to save memory to disk. Defaults to False.
            memory_file (str, optional): File path to save memory when persisting. Defaults to "AvalAgent/agent_memory.json".

        Raises:
            ValueError: If api_key or base_url is empty, None, or if api_key.get_secret_value() is None.
        """
        self.logger = get_logger()

        if not api_key or not base_url:
            self.logger.error("API key and base URL must be provided.")
            raise ValueError("API key and base URL are required.")
        if type(api_key) is not str and api_key.get_secret_value() is None:
            self.logger.error("API key is None; ensure you have set up your secret key.")
            raise ValueError("API key cannot be None.")

        if type(api_key) is str:
            api_key = SecretStr(api_key)

        self.api_key = api_key
        self.base_url = base_url
        self.stop_after_attempt = stop_after_attempt
        self.model_priority_list = model_priority_list or [
                "gpt-4o",
                "gemini-2.5-pro-preview-03-25",
                "anthropic.claude-3-5-sonnet-20241022-v2:0"
        ]

        # Memory-related attributes
        self.use_memory = use_memory
        self.max_memory_size = max_memory_size
        self.persist_memory = persist_memory
        self.memory_file = memory_file
        self._memory: List[Dict[str, Any]] = []

        if self.use_memory and self.persist_memory:
            self.load_memory()

    def add_to_memory(self, role: str, content: str) -> None:
        """Add a new message to the conversation memory.

        Args:
            role (str): The role of the message sender ('user', 'assistant', or 'system').
            content (str): The content of the message.
        """
        if not self.use_memory:
            return

        self._memory.append({"role": role, "content": content})

        # Trim memory if it exceeds max size
        if len(self._memory) > self.max_memory_size:
            self._memory = self._memory[-self.max_memory_size:]

        if self.persist_memory:
            self.save_memory()

    def get_memory(self, as_string: bool = False) -> Union[List[Dict[str, Any]], str]:
        """Retrieve the conversation memory.

        Args:
            as_string (bool, optional): Whether to return memory as formatted string.
                Defaults to False (returns raw memory list).

        Returns:
            Union[List[Dict[str, Any]], str]: The conversation memory in requested format.
        """
        if not self.use_memory:
            return "" if as_string else []

        if as_string:
            memory_str = "\n".join(
                    f"{msg['role'].upper()}: {msg['content']}"
                    for msg in self._memory
            )
            return memory_str
        return self._memory.copy()

    def clear_memory(self) -> None:
        """Clear the conversation memory."""
        self._memory = []
        if self.persist_memory:
            self.save_memory()

    def save_memory(self) -> None:
        """Save the conversation memory to disk."""
        if not self.use_memory or not self.persist_memory:
            return

        try:
            # Create directory if it doesn't exist
            Path(self.memory_file).parent.mkdir(parents=True, exist_ok=True)

            with open(self.memory_file, 'w') as f:
                json.dump(self._memory, f)
        except Exception as e:
            self.logger.error(f"Failed to save memory: {e}")

    def load_memory(self) -> None:
        """Load conversation memory from disk."""
        if not self.use_memory or not self.persist_memory:
            return

        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    self._memory = json.load(f)
                    # Ensure we don't exceed max memory size
                    if len(self._memory) > self.max_memory_size:
                        self._memory = self._memory[-self.max_memory_size:]
        except Exception as e:
            self.logger.error(f"Failed to load memory: {e}")
            self._memory = []

    def get_response(self, system_prompt: str, query: str, model: str = None, temperature: float = 0.1,
                     use_memory: bool = None) -> str | None:
        """Get a response from the AI model using the provided prompt and query.

        Args:
            system_prompt (str): The system prompt to set the context for the AI model.
            query (str): The user's query to send to the AI model.
            model (str, optional): The specific model to use. Defaults to the first model in model_priority_list.
            temperature (float, optional): The temperature for the model, controlling response randomness.
                Defaults to 0.1.
            use_memory (bool, optional): Override for instance-level use_memory setting. Defaults to None (use instance setting).

        Returns:
            str | None: The response content from the AI model, or None if all attempts fail.

        Raises:
            ValueError: If the query is empty or None.
            requests.exceptions.RequestException: If a network error occurs during the API request.
            RateLimitError: If the API rate limit is exceeded.
        """
        if not query or query.strip() == "":
            self.logger.error("Query is empty or None.")
            raise ValueError("Query cannot be empty or None.")

        # Determine memory usage
        current_use_memory = self.use_memory if use_memory is None else use_memory

        # Prepare messages
        messages = []

        if current_use_memory:
            memory_content = self.get_memory(as_string=True)
            enhanced_system_prompt = (
                    "Here is the history of our conversation. Use it if relevant:\n"
                    f"{memory_content}\n\n"
                    f"{system_prompt}"
            )
            messages.append(SystemMessage(content=enhanced_system_prompt))
        else:
            messages.append(SystemMessage(content=system_prompt))

        messages.append(HumanMessage(content=query))

        current_model = model or self.model_priority_list[0]

        for attempt in range(self.stop_after_attempt):
            try:
                llm = ChatOpenAI(
                        model=current_model,
                        api_key=self.api_key,
                        base_url=self.base_url,
                        temperature=temperature
                )
                response = llm.invoke(messages)
                response_content = response.content.strip()

                # Add to memory if enabled
                if current_use_memory:
                    self.add_to_memory("user", query)
                    self.add_to_memory("assistant", response_content)

                return response_content
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Network error (attempt {attempt + 1}): {e}")
            except RateLimitError as e:
                self.logger.error(f"Attempt {attempt + 1} failed due to quota exceeded: {e}")
                return None
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")

        return None

    def get_credit_info(self) -> dict:
        """Fetches the user's credit information from the API.

        Returns:
            dict: A dictionary containing the credit information with keys:
                - limit
                - remaining_irt
                - remaining_unit
                - total_unit
                - exchange_rate
                Returns empty dict if request fails.
        """
        url = "https://api.avalai.ir/user/credit"
        headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key.get_secret_value()}"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch credit info: {e}")
            return {}

    def log_credit_info_table(self, credit_info: dict = None) -> None:
        """Logs the credit information in a formatted table.

        Args:
            credit_info (dict, optional): Credit info dictionary to display.
                If None, will fetch fresh data. Defaults to None.
        """
        if credit_info is None:
            credit_info = self.get_credit_info()

        if not credit_info:
            self.logger.error("No credit information available to display")
            return

        table_headers = ["Metric", "Value"]
        table_rows = [
                ("Limit", credit_info.get('limit', 'N/A')),
                ("Remaining IRT", credit_info.get('remaining_irt', 'N/A')),
                ("Remaining Unit", credit_info.get('remaining_unit', 'N/A')),
                ("Total Unit", credit_info.get('total_unit', 'N/A')),
                ("Exchange Rate", credit_info.get('exchange_rate', 'N/A'))
        ]
        table = tabulate(table_rows, headers=table_headers, tablefmt="grid")
        self.logger.info("\n" + table)