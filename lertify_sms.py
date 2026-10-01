"""
lertify_sms.py

Python client for the Lertify SMS API.
Created by: Jasec

Install:
    pip install requests
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Union

import requests
from requests import Response
from requests.exceptions import RequestException


class TextAnalyzer:
    """
    Utilities for analyzing SMS text.
    """

    @staticmethod
    def determine_encoding(text: str) -> str:
        """
        Return 'Unicode' when the text contains non-ASCII characters.
        Otherwise return 'ASCII'.
        """
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        return "Unicode" if not text.isascii() else "ASCII"

    @classmethod
    def is_unicode(cls, text: str) -> bool:
        """
        Return the boolean value required by the Lertify API.
        """
        return cls.determine_encoding(text) == "Unicode"

    @classmethod
    def analyze(cls, text: str) -> Dict[str, Union[str, bool]]:
        """
        Analyze text encoding.
        """
        return {
            "text": text,
            "encoding": cls.determine_encoding(text),
            "isUnicode": cls.is_unicode(text),
        }


class LertifyAPIError(Exception):
    """
    Raised when the Lertify API returns an HTTP error.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}

    def __str__(self) -> str:
        if self.status_code is not None:
            return f"Lertify API error ({self.status_code}): {self.message}"

        return f"Lertify API error: {self.message}"


class LertifyNetworkError(Exception):
    """
    Raised when the API request cannot be completed because of a network error.
    """


class LertifySMSClient:
    """
    Client for the Lertify SMS API.

    The API endpoint is:

        POST https://api.lertify.app/v1/sms/messages
    """

    DEFAULT_ENDPOINT = "https://api.lertify.app/v1/sms/messages"
    MAX_MESSAGE_LENGTH = 640

    # E.164 format, for example: +38640123456
    E164_PATTERN = re.compile(r"^\+[1-9]\d{6,14}$")

    # Common sender-name format.
    # Allows letters, numbers, spaces, dots, underscores and hyphens.
    SENDER_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{0,10}$")

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = 30.0,
        endpoint: str = DEFAULT_ENDPOINT,
        session: Optional[requests.Session] = None,
    ) -> None:
        """
        Initialize the Lertify SMS client.

        Args:
            api_key:
                Lertify API key.

            timeout:
                HTTP request timeout in seconds.

            endpoint:
                Lertify API endpoint.

            session:
                Optional requests.Session instance.
        """
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("api_key must not be empty")

        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")

        self.api_key = api_key.strip()
        self.timeout = timeout
        self.endpoint = endpoint
        self.session = session or requests.Session()

    @staticmethod
    def get_unix_timestamp() -> int:
        """
        Return the current UTC time as a Unix timestamp in seconds.
        """
        return int(datetime.now(timezone.utc).timestamp())

    @staticmethod
    def datetime_to_unix_timestamp(value: datetime) -> int:
        """
        Convert a datetime to a Unix timestamp.

        Naive datetimes are treated as UTC.
        Timezone-aware datetimes are converted to UTC.
        """
        if not isinstance(value, datetime):
            raise TypeError("value must be a datetime object")

        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)

        return int(value.timestamp())

    def send_sms(
        self,
        *,
        sender: str,
        destinations: Union[str, Iterable[str]],
        content: str,
        is_unicode: Optional[bool] = None,
        delivery_report_url: Optional[str] = None,
        scheduled_time: Optional[Union[int, datetime]] = None,
        price_report: bool = False,
    ) -> Dict[str, Any]:
        """
        Send an SMS immediately or schedule it.

        Args:
            sender:
                Sender name or phone number.

                Examples:
                    "Lertify01"
                    "+38640123456"

            destinations:
                One destination or multiple destinations.

                Examples:
                    "+38640123456"

                    [
                        "+38640123456",
                        "+38640987654",
                    ]

            content:
                SMS content. Maximum 640 characters.

            is_unicode:
                If None, Unicode is detected automatically.
                Set True or False to override automatic detection.

            delivery_report_url:
                Optional public webhook URL for delivery reports.

            scheduled_time:
                Unix timestamp in seconds or a datetime object.

                If None:
                    The message is sent immediately.

                If in the future:
                    The message is scheduled.

                If equal to or earlier than the current time:
                    Lertify sends it immediately.

            price_report:
                If True, delivery reports may include message pricing.

        Returns:
            The JSON response returned by Lertify.
        """
        self._validate_sender(sender)
        self._validate_content(content)

        normalized_destinations = self._normalize_destinations(
            destinations
        )

        if is_unicode is None:
            is_unicode = TextAnalyzer.is_unicode(content)

        if not isinstance(is_unicode, bool):
            raise ValueError("is_unicode must be True, False, or None")

        if scheduled_time is not None:
            if isinstance(scheduled_time, datetime):
                scheduled_time = self.datetime_to_unix_timestamp(scheduled_time)
            self._validate_scheduled_time(scheduled_time)

        payload: Dict[str, Any] = {
            "sender": sender,
            "destinations": normalized_destinations,
            "message": {
                "content": content,
                "isUnicode": is_unicode,
            },
            "priceReport": price_report,
        }

        if delivery_report_url is not None:
            if not isinstance(delivery_report_url, str):
                raise ValueError("delivery_report_url must be a string")

            if not delivery_report_url.strip():
                raise ValueError(
                    "delivery_report_url must not be empty"
                )

            payload["deliveryReportUrl"] = delivery_report_url

        if scheduled_time is not None:
            payload["scheduledTime"] = scheduled_time

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "apikey": self.api_key,
        }

        try:
            response = self.session.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except RequestException as exc:
            raise LertifyNetworkError(
                f"Could not connect to the Lertify API: {exc}"
            ) from exc

        return self._handle_response(response)

    @classmethod
    def _validate_sender(cls, sender: str) -> None:
        """
        Validate a sender name or sender phone number.

        Accepted examples:

            "Lertify01"
            "+38640123456"
        """
        if not isinstance(sender, str) or not sender.strip():
            raise ValueError("sender must not be empty")

        sender = sender.strip()

        if cls.E164_PATTERN.fullmatch(sender):
            return

        if cls.SENDER_NAME_PATTERN.fullmatch(sender):
            return

        raise ValueError(
            f"Invalid sender '{sender}'. Sender must be either an "
            "alphanumeric sender name or an E.164 phone number such as "
            "'+38640123456'."
        )

    def _validate_content(self, content: str) -> None:
        """
        Validate SMS content.
        """
        if not isinstance(content, str):
            raise ValueError("content must be a string")

        if not content.strip():
            raise ValueError(
                "content must not be empty or whitespace only"
            )

        if len(content) > self.MAX_MESSAGE_LENGTH:
            raise ValueError(
                f"content must not exceed "
                f"{self.MAX_MESSAGE_LENGTH} characters"
            )

    def _normalize_destinations(
        self,
        destinations: Union[str, Iterable[str]],
    ) -> List[str]:
        """
        Convert one or multiple destinations to a validated list.
        """
        if isinstance(destinations, str):
            result = [destinations]
        else:
            result = list(destinations)

        if not result:
            raise ValueError(
                "destinations must contain at least one phone number"
            )

        for destination in result:
            if not isinstance(destination, str):
                raise ValueError(
                    "Each destination must be a string"
                )

            if not self.E164_PATTERN.fullmatch(destination):
                raise ValueError(
                    f"Invalid destination '{destination}'. "
                    "Use E.164 format, for example '+38640123456'."
                )

        return result

    @staticmethod
    def _validate_scheduled_time(scheduled_time: int) -> None:
        """
        Validate a Unix timestamp.
        """
        if isinstance(scheduled_time, bool):
            raise ValueError(
                "scheduled_time must be an integer"
            )

        if not isinstance(scheduled_time, int):
            raise ValueError(
                "scheduled_time must be an integer Unix timestamp"
            )

        if scheduled_time < 0:
            raise ValueError(
                "scheduled_time must not be negative"
            )

    @staticmethod
    def _handle_response(response: Response) -> Dict[str, Any]:
        """
        Process the API response.

        Successful requests return HTTP 202.
        """
        try:
            data = response.json()
        except ValueError:
            data = {
                "error": response.text or "The API returned invalid JSON"
            }

        if response.status_code != 202:
            if isinstance(data, dict):
                error_message = data.get(
                    "error",
                    response.text or "Unknown API error",
                )
            else:
                error_message = response.text or "Unknown API error"

            raise LertifyAPIError(
                message=str(error_message),
                status_code=response.status_code,
                response_data=data if isinstance(data, dict) else {},
            )

        if not isinstance(data, dict):
            raise LertifyAPIError(
                message="The API returned an unexpected response format",
                status_code=response.status_code,
            )

        return data