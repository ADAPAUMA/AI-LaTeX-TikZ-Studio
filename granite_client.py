"""
granite_client.py
-----------------
Handles all communication with the IBM Granite language model via the
IBM watsonx.ai REST API.

Configuration can be read from environment variables or passed at runtime:
    WATSONX_API_KEY    – IBM Cloud IAM API key
    WATSONX_URL        – watsonx.ai service URL (e.g. https://us-south.ml.cloud.ibm.com)
    WATSONX_PROJECT_ID – watsonx.ai project ID

Optional:
    GRANITE_MODEL_ID   – defaults to "ibm/granite-13b-instruct-v2"
"""

import os
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
DEFAULT_MODEL_ID = "ibm/granite-13b-instruct-v2"
DEFAULT_WATSONX_URL = "https://us-south.ml.cloud.ibm.com"

GENERATE_PATH = "/ml/v1/text/generation?version=2023-05-29"


class GraniteClientError(Exception):
    """Raised when the IBM Granite API returns an error or is unreachable."""


class GraniteClient:
    """
    Thin wrapper around the IBM watsonx.ai text-generation REST API.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        project_id: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> None:
        self._api_key = api_key or os.getenv("WATSONX_API_KEY")
        self._base_url = (base_url or os.getenv("WATSONX_URL", DEFAULT_WATSONX_URL)).rstrip("/")
        self._project_id = project_id or os.getenv("WATSONX_PROJECT_ID")
        self._model_id = model_id or os.getenv("GRANITE_MODEL_ID", DEFAULT_MODEL_ID)
        self._iam_token: Optional[str] = None

    def is_configured(self) -> bool:
        """Return True if required credentials are set."""
        return bool(self._api_key and self._base_url and self._project_id)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 2048,
        temperature: float = 0.2,
        top_p: float = 0.9,
        repetition_penalty: float = 1.1,
        stop_sequences: Optional[list[str]] = None,
    ) -> str:
        """
        Send *prompt* to IBM Granite and return the generated text.
        """
        if not self.is_configured():
            missing = []
            if not self._api_key: missing.append("WATSONX_API_KEY")
            if not self._project_id: missing.append("WATSONX_PROJECT_ID")
            raise GraniteClientError(
                f"IBM watsonx credentials missing: {', '.join(missing)}. "
                "Configure them in sidebar settings or .env file."
            )

        token = self._get_iam_token()
        url = f"{self._base_url}{GENERATE_PATH}"

        payload: dict = {
            "model_id": self._model_id,
            "project_id": self._project_id,
            "input": prompt,
            "parameters": {
                "decoding_method": "greedy" if temperature == 0 else "sample",
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "repetition_penalty": repetition_penalty,
            },
        }
        if stop_sequences:
            payload["parameters"]["stop_sequences"] = stop_sequences

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
        except requests.exceptions.ConnectionError as exc:
            raise GraniteClientError(
                "Cannot connect to IBM watsonx.ai. "
                "Check WATSONX_URL and your network connection."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise GraniteClientError(
                "Request to IBM watsonx.ai timed out. "
                "The model may be busy — please try again."
            ) from exc

        if response.status_code == 401:
            # Token may have expired — refresh and retry once
            logger.debug("401 received; refreshing IAM token and retrying.")
            self._iam_token = None
            token = self._get_iam_token()
            headers["Authorization"] = f"Bearer {token}"
            response = requests.post(url, json=payload, headers=headers, timeout=120)

        if not response.ok:
            raise GraniteClientError(
                f"IBM watsonx.ai API error {response.status_code}: "
                f"{response.text[:400]}"
            )

        data = response.json()
        try:
            generated_text: str = data["results"][0]["generated_text"]
        except (KeyError, IndexError) as exc:
            raise GraniteClientError(
                f"Unexpected API response structure: {str(data)[:400]}"
            ) from exc

        return generated_text.strip()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_iam_token(self) -> str:
        """Return a cached IAM bearer token, refreshing it when absent."""
        if self._iam_token:
            return self._iam_token
        if not self._api_key:
            raise GraniteClientError("WATSONX_API_KEY is not configured.")
        self._iam_token = self._fetch_iam_token(self._api_key)
        return self._iam_token

    @staticmethod
    def _fetch_iam_token(api_key: str) -> str:
        """Exchange an IBM Cloud API key for a short-lived IAM bearer token."""
        try:
            response = requests.post(
                IAM_TOKEN_URL,
                data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey": api_key,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
            )
        except requests.exceptions.RequestException as exc:
            raise GraniteClientError(
                "Failed to obtain IAM token from IBM Cloud."
            ) from exc

        if not response.ok:
            raise GraniteClientError(
                f"IAM token request failed ({response.status_code}). "
                "Check your WATSONX_API_KEY."
            )

        return response.json()["access_token"]
