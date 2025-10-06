import httpx
import asyncio
import logging
from dotenv import dotenv_values
from pathlib import Path

# Get the absolute path to the .env file
env_path = Path(__file__).parent.parent.parent / ".env"
config = dotenv_values(str(env_path))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, base_url: str = config['INFERENCE_SERVER_URL'], timeout: float = 180.0):
        """Initialize the LLM client.
        
        Args:
            base_url: Base URL of the LLM inference server
            timeout: Request timeout in seconds (default: 180 seconds / 3 minutes)
        """
        self.base_url = base_url
        self.timeout = timeout
        self._client = None
        
    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def generate_text(self, prompt: str, max_tokens: int = 100, temperature: float = 0.7) -> dict:
        """Generate text from the LLM.
        
        Args:
            prompt: The input prompt for the LLM
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (0.0 to 1.0)
            
        Returns:
            dict: The LLM response
            
        Raises:
            Exception: If there's an error generating the text
        """
        payload = {
            "model": config['MODEL_NAME'],
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            logger.info(f"Sending request to {self.base_url} (timeout: {self.timeout}s) with payload: {payload}")
            
            if not self._client:
                self._client = httpx.AsyncClient(timeout=self.timeout)
                
            response = await self._client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
                
            # Log response size for debugging
            response_size = len(str(result).encode('utf-8'))
            logger.info(f"Successfully received response from LLM (size: {response_size} bytes)")
                
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
            error_msg = f"Request timed out after {self.timeout} seconds. The LLM server is not responding or the request is taking too long."
            logger.error(error_msg)
            # Include timeout value in the error message for better debugging
            raise TimeoutError(error_msg) from None
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception(error_msg)  # Log full stack trace for debugging
            raise  # Re-raise the exception to be handled by the caller
            raise Exception(error_msg) from e