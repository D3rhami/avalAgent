import json
import os
from pathlib import Path
from typing import Any, Dict, List, Union

import requests
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from openai import RateLimitError
from pydantic import SecretStr
from tabulate import tabulate

from avalAgent.logger import get_logger


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

    def get_response(self, system_prompt: str, query: str, **config) -> str | None:
        """Get a response from the AI model using the provided prompt and query.

        Args:
            system_prompt (str): The system prompt to set the context for the AI model.
            query (str): The user's query to send to the AI model.
            **config: Additional configuration parameters:
                - model (str): The specific model to use. Required.
                - temperature (float, optional): Controls response randomness (0.0-1.0). Defaults to 0.1.
                - use_memory (bool, optional): Whether to use conversation memory. Defaults to instance setting.

        Returns:
            str | None: The response content from the AI model, or None if:
                - Query is empty or None
                - Model is not specified
                - All attempts fail
                - Rate limit exceeded

        """
        if not query or query.strip() == "":
            self.logger.error("Query is empty or None.")
            return None

        # Get configuration values with defaults
        model = config.get("model")
        temperature = config.get("temperature", 0.1)
        use_memory = config.get("use_memory")

        # Validate model if specified
        if not model or not isinstance(model, str) or model.strip() == "":
            self.logger.error("Model name must be a non-empty string")
            return None

        # Prepare messages
        messages = [SystemMessage(
                content=f"{self.get_memory(as_string=True)}\n\n{system_prompt}"
                if (self.use_memory if use_memory is None else use_memory)
                else system_prompt
        ), HumanMessage(content=query)]

        for attempt in range(self.stop_after_attempt):
            try:
                llm = ChatOpenAI(
                        model=model,
                        api_key=self.api_key,
                        base_url=self.base_url,
                        temperature=temperature
                )
                response = llm.invoke(messages)
                response_content = response.content.strip()

                if use_memory or (use_memory is None and self.use_memory):
                    self.add_to_memory("user", query)
                    self.add_to_memory("assistant", response_content)

                return response_content
            except RateLimitError as e:
                self.logger.error(f"Rate limit exceeded on attempt {attempt + 1}: {e}")
                return None
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Network error on attempt {attempt + 1}: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")

        return None

    def enhance_prompt(self, raw_prompt: str, **config) -> str | None:
        """
        Enhances a raw prompt into a structured format using AI analysis.

        Args:
            raw_prompt (str): The unprocessed prompt to enhance. Cannot be empty.
            **config: Additional configuration parameters:
                - model (str, optional): Model to use for enhancement. Defaults to "gpt-4o".
                - temperature (float, optional): Controls response randomness. Defaults to 0.2.
                - use_memory (bool, optional): Whether to use conversation memory. Defaults to False.

        Returns:
            str | None: The enhanced prompt, or None if enhancement failed.
        """
        import re

        if not raw_prompt or not isinstance(raw_prompt, str) or raw_prompt.strip() == "":
            self.logger.error("Raw prompt cannot be empty")
            return None

        try:
            with open("pm.json", "r") as f:
                system_prompt = json.load(f).get("sp_enhanced", "")

            response = self.get_response(
                    system_prompt=system_prompt,
                    query=raw_prompt,
                    model=config.get("model", "gpt-4o"),
                    temperature=config.get("temperature", 0.2),
                    use_memory=config.get("use_memory", False)
            )

            if not response:
                return None

            # Attempt to extract the first JSON block from the response
            json_match = re.search(r'\{.*?}', response.lower(), re.DOTALL)
            if not json_match:
                self.logger.warning("No JSON found in AI response")
                return None

            try:
                structured_data = json.loads(json_match.group())
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse JSON: {e}")
                return None

            # Required fields with defaults
            defaults = {
                    "goal": "None",
                    "role": "None",
                    "knowledge": [],
                    "input_formats": [],
                    "output_formats": [],
                    "strict_rules": []
            }

            for key, default in defaults.items():
                structured_data[key] = structured_data.get(key, default)

            # Optional fields
            examples = structured_data.get("examples", [])
            ignores = structured_data.get("ignores", [])

            enhanced_prompt = self.create_structured_prompt(
                    goal=structured_data["goal"],
                    role=structured_data["role"],
                    knowledge=structured_data["knowledge"],
                    input_formats=structured_data["input_formats"],
                    output_formats=structured_data["output_formats"],
                    strict_rules=structured_data["strict_rules"],
                    examples=examples,
                    ignores=ignores
            )

            return enhanced_prompt

        except Exception as e:
            self.logger.error(f"Prompt enhancement failed: {e}")
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

    def create_structured_prompt(
            self,
            goal: str,
            role: str,
            knowledge: str,
            input_formats: List[str],
            output_formats: str,
            strict_rules: List[str],
            examples: List[str] = None,
            ignores: List[str] = None
    ) -> str | None:
        """Creates a well-structured prompt from components.

        Args:
            goal (str): Primary objective of the prompt. Required.
            role (str): AI's role/persona. Required.
            knowledge (str): Background information. Required.
            input_formats (List[str]): Expected input structures. Required.
            output_formats (str): Required output structure. Required.
            strict_rules (List[str]): Non-negotiable rules. Required.
            examples (List[str], optional): Example inputs/outputs. Defaults to None.
            ignores (List[str], optional): Things to avoid. Defaults to None.

        Returns:
            str | None: Formatted prompt string, or None if:
                - Any required field is empty/None
                - input_formats/strict_rules are empty lists

        Raises:
            TypeError: If any list argument is not a list.
        """
        # Validate required arguments
        required_args = {
                "goal": goal,
                "role": role,
                "knowledge": knowledge,
                "output_formats": output_formats
        }

        for name, value in required_args.items():
            if not value or not isinstance(value, str) or value.strip() == "":
                self.logger.error(f"{name} cannot be empty")
                return None

        # Validate list arguments
        list_args = {
                "input_formats": input_formats,
                "strict_rules": strict_rules,
                "examples": examples or [],
                "ignores": ignores or []
        }

        for name, value in list_args.items():
            if not isinstance(value, list):
                self.logger.error(f"{name} must be a list")
                raise TypeError(f"{name} must be a list")
            if name in ["input_formats", "strict_rules"] and not value:
                self.logger.error(f"{name} cannot be empty")
                return None

        # Build prompt sections
        sections = [
                f"# YOUR ROLE: {role}\n\n",
                f"# YOUR GOAL: {goal}\n\n",
                f"## KNOWLEDGE BASE:\n{knowledge}\n\n",
                "# INPUT FORMATS:"
        ]

        sections.extend(f"\n{i}. {fmt}" for i, fmt in enumerate(input_formats, 1))
        sections.append("\n\n# OUTPUT FORMAT REQUIREMENTS:\n{output_formats}\n\n")
        sections.append("# STRICT RULES:\n" + "\n- ".join([""] + strict_rules))

        if examples:
            sections.append("\n\n## EXAMPLES:" + "".join(f"\n- {ex}" for ex in examples))

        if ignores:
            sections.append("\n\n## IGNORE:" + "".join(f"\n- {item}" for item in ignores))

        return "".join(sections)
