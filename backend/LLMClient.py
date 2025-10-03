import httpx
import asyncio
import logging
from dotenv import dotenv_values

config = dotenv_values("../.env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, base_url: str = config['INFERENCE_SERVER_URL']):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0) 

    async def generate_text(self, prompt: str, max_tokens: int = 100, temperature: float = 0.7) -> dict:
        """Generate text from the LLM."""
        payload = {
            "model": config['MODEL_NAME'],
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            logger.info(f"Sending request to {self.base_url} with payload: {payload}")
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            logger.info("Successfully received response from LLM")
            return result
        except httpx.ConnectError as e:
            error_msg = f"Failed to connect to LLM server at {self.base_url}. Is the server running?"
            logger.error(error_msg)
            raise Exception(error_msg) from e
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
        except httpx.ReadTimeout:
            error_msg = "Request timed out. The LLM server is not responding."
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e