"""
Embedding service for generating vector embeddings using AWS API Gateway.
Uses the same embedding service as the FastAPI version for consistency.
"""

import json
import logging
import os
from typing import List, Optional
from urllib.parse import urlparse

import botocore
import botocore.credentials
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using AWS API Gateway."""

    def __init__(self) -> None:
        """Initialize the embedding service with AWS configuration."""
        self.embedding_dimension = 768
        self.aws_access_key_id = os.environ.get("AWS_ACCESS_KEY")
        self.aws_secret_access_key = os.environ.get("AWS_SECRET_KEY")
        self.api_gateway_url = os.environ.get("AWS_EMBED_URL")
        self.api_key = os.environ.get("AWS_APP_RUNNER_API_KEY", "")

        # Validate required environment variables
        if not all(
            [self.aws_access_key_id, self.aws_secret_access_key, self.api_gateway_url]
        ):
            raise ValueError(
                "AWS_ACCESS_KEY, AWS_SECRET_KEY, and AWS_EMBED_URL "
                "environment variables must be set."
            )

        # Parse region from URL
        self._region, self._hostname = self._parse_api_gateway_url()

    def _parse_api_gateway_url(self) -> tuple[str, str]:
        """Parse region and hostname from API Gateway URL."""
        try:
            parsed_url = urlparse(self.api_gateway_url)
            hostname = parsed_url.hostname

            if not hostname or not isinstance(hostname, str):
                raise ValueError(f"Invalid API Gateway URL: {self.api_gateway_url}")

            # Extract region from hostname
            parts = hostname.split(".")
            if len(parts) < 3 or "execute-api" not in parts:
                raise ValueError(
                    f"Invalid API Gateway URL format: {self.api_gateway_url}. "
                    "Expected format: https://{{id}}.execute-api.{{region}}.amazonaws.com/..."
                )

            region = parts[
                2
            ]  # e.g., 'us-east-1' from 'id.execute-api.us-east-1.amazonaws.com'
            return region, hostname

        except Exception as e:
            logger.error(f"Failed to parse API Gateway URL: {str(e)}")
            raise ValueError(f"Invalid API Gateway URL: {self.api_gateway_url}")

    def _call_api_gateway_with_iam_auth(self, payload: dict) -> dict:
        """Call AWS API Gateway endpoint with IAM authentication."""
        # Create credentials object
        credentials = botocore.credentials.Credentials(
            access_key=self.aws_access_key_id, secret_key=self.aws_secret_access_key
        )

        # Create an AWSRequest object for signing
        request = AWSRequest(
            method="POST",
            url=self.api_gateway_url,
            data=json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "Host": self._hostname,
                "x-api-key": self.api_key,
            },
        )

        # Sign the request
        SigV4Auth(credentials, "execute-api", self._region).add_auth(request)

        # Prepare the signed request for requests
        prepared_request = request.prepare()

        # Make the HTTP request
        try:
            logger.debug(f"Making POST request to {self.api_gateway_url}")
            response = requests.request(
                prepared_request.method,
                prepared_request.url,
                headers=prepared_request.headers,
                data=prepared_request.body,
                timeout=30,
            )
            response.raise_for_status()

            # Validate response format
            try:
                result = response.json()
                if not isinstance(result, dict):
                    raise ValueError("Response is not a JSON object")
                return result
            except json.JSONDecodeError:
                logger.error(f"Failed to parse response as JSON: {response.text}")
                raise ValueError("Invalid JSON response from API Gateway")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling API Gateway: {str(e)}")
            if e.response is not None:
                logger.error(f"Response Status Code: {e.response.status_code}")
                logger.error(f"Response Body: {e.response.text}")
            raise

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _get_embedding_with_retry(self, text: str) -> List[float]:
        """Get embedding from AWS endpoint with retry logic."""
        try:
            response = self._call_api_gateway_with_iam_auth({"text": text})
            embedding = response["embedding"]

            if (
                not isinstance(embedding, list)
                or len(embedding) != self.embedding_dimension
            ):
                raise ValueError(
                    f"Invalid embedding format or dimension: {len(embedding) if isinstance(embedding, list) else 'not a list'}"
                )

            return embedding

        except Exception as e:
            logger.error(f"Error in _get_embedding_with_retry: {str(e)}")
            raise

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text string using AWS API.

        Args:
            text: The text to generate embedding for

        Returns:
            List of floats representing the embedding, or None if failed
        """
        if not text or not text.strip():
            return None

        try:
            # Use AWS API to generate embedding
            embedding = self._get_embedding_with_retry(text.strip())
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {e}")
            return None

    def generate_embeddings(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple text strings using AWS API.

        Args:
            texts: List of texts to generate embeddings for

        Returns:
            List of embeddings (or None for failed generations)
        """
        if not texts:
            return []

        result: List[Optional[List[float]]] = []
        for text in texts:
            if text and text.strip():
                try:
                    embedding = self._get_embedding_with_retry(text.strip())
                    result.append(embedding)
                except Exception as e:
                    logger.error(f"Failed to generate embedding for text '{text}': {e}")
                    result.append(None)
            else:
                result.append(None)

        return result


# Global instance for reuse
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
