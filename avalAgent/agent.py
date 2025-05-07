from typing import List

import requests
from langchain_core.messages import HumanMessage, SystemMessage
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

    def __init__(self, api_key: SecretStr | str, base_url: str = 'https://api.avalai.ir/v1',
                 model_priority_list: List[str] = None,
                 stop_after_attempt: int = 3):
        """Initialize the avalAgent with API credentials and configuration.

        Args:
            api_key (SecretStr): The API key for authentication.
            base_url (str, optional): The base URL of the API. Defaults to 'https://api.avalai.ir/v1'.
            model_priority_list (List[str], optional): A list of model names to try in order.
                Defaults to ["gpt-4o", "deepseek-chat", "anthropic.claude-3-5-sonnet-20241022-v2:0"].
            stop_after_attempt (int, optional): Maximum number of retry attempts. Defaults to 3.

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
                "deepseek-chat",
                "anthropic.claude-3-5-sonnet-20241022-v2:0"
        ]

    def get_response(self, system_prompt: str, query: str, model: str = None, temperature: float = 0.1) -> str | None:
        """Get a response from the AI model using the provided prompt and query.

        Args:
            system_prompt (str): The system prompt to set the context for the AI model.
            query (str): The user's query to send to the AI model.
            model (str, optional): The specific model to use. Defaults to the first model in model_priority_list.
            temperature (float, optional): The temperature for the model, controlling response randomness.
                Defaults to 0.1.

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

        current_model = model or self.model_priority_list[0]

        for attempt in range(self.stop_after_attempt):
            try:
                llm = ChatOpenAI(model=current_model, api_key=self.api_key, base_url=self.base_url,
                                 temperature=temperature)
                response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=query)])
                return response.content.strip()
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Network error (attempt {attempt + 1}): {e}")
            except RateLimitError as e:
                self.logger.error(f"Attempt {attempt + 1} failed due to quota exceeded: {e}")
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")

        return None

    def get_credit_info(self):
        """Fetches the user's credit information and logs it in a formatted table."""
        url = "https://api.avalai.ir/user/credit"
        headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key.get_secret_value()}"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            credit_info = response.json()

            # Log the information in a nice table format
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

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch credit info: {e}")
