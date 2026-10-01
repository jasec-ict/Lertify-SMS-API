```markdown
# Lertify SMS Python Client
## Lertify-SMS-API
A Python client library for interacting with the Lertify SMS API. Easily send immediate SMS messages, schedule deliveries, send Unicode content, track prices, and handle API errors cleanly.

Python client for the Lertify SMS API for https://lertify.app
Read more: https://lertify.com

---

## Table of Contents
- [Lertify SMS Python Client](#lertify-sms-python-client)
  - [Lertify-SMS-API](#lertify-sms-api)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [(back to top)](#back-to-top)
  - [Authentication \& Setup](#authentication--setup)
  - [(back to top)](#back-to-top-1)
  - [Usage Examples](#usage-examples)
    - [Send Immediately](#send-immediately)
  - [(back to top)](#back-to-top-2)
    - [Send to Multiple Numbers](#send-to-multiple-numbers)
    - [Unicode Support](#unicode-support)
  - [(back to top)](#back-to-top-3)
    - [Delivery Reports \& Price Reporting](#delivery-reports--price-reporting)
  - [(back to top)](#back-to-top-4)
    - [Scheduling Messages](#scheduling-messages)
  - [(back to top)](#back-to-top-5)
  - [Error Handling](#error-handling)
  - [(back to top)](#back-to-top-6)
  - [Complete Application Example](#complete-application-example)
  - [(back to top)](#back-to-top-7)
  - [Contributing](#contributing)
    - [Top contributors:](#top-contributors)
  - [License](#license)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Installation

Install the library using `pip`:

```bash
pip install requests

```

## Authentication & Setup

Import the module:

```python
from lertify_sms import LertifySMSClient

```

The API key should preferably be stored in an environment variable:

**Linux / macOS:**

```bash
export LERTIFY_API_KEY="YOUR_API_KEY"

```

**Windows PowerShell:**

```powershell
$env:LERTIFY_API_KEY="YOUR_API_KEY"

```

Then load it in Python:

```python
import os
from lertify_sms import LertifySMSClient

client = LertifySMSClient(
    api_key=os.environ["LERTIFY_API_KEY"]
)

```

## Usage Examples

### Send Immediately

The sender parameter accepts both custom sender names (e.g., `"Lertify01"`) and phone numbers (e.g., `"+38640123456"`). Omitting `scheduled_time` automatically sends the message immediately.

**Using a sender name:**

```python
response = client.send_sms(
    sender="Lertify01",
    destinations="+38640123456",
    content="Hello from Python!",
)
print(response)

```

**Using a sender phone number:**

```python
response = client.send_sms(
    sender="+38640123456",
    destinations="+38640987654",
    content="Hello from a phone-number sender!",
)
print(response)

```

### Send to Multiple Numbers

Pass a list or tuple of phone numbers to send to multiple recipients simultaneously.

**Using a list:**

```python
recipients = [
    "+38640123456",
    "+38640987654",
    "+38641111222",
]

response = client.send_sms(
    sender="Lertify01",
    destinations=recipients,
    content="This SMS is sent to multiple recipients.",
)
print(response)

```

---

### Unicode Support

Unicode characters are detected automatically:

```python
response = client.send_sms(
    sender="Lertify01",
    destinations="+38640123456",
    content="To je testno sporočilo čšž.",
)
print(response)

```

Generated payload automatically sets `isUnicode`:

```json
{
  "message": {
    "content": "To je testno sporočilo čšž.",
    "isUnicode": true
  }
}

```

You can also manually override the encoding:

```python
response = client.send_sms(
    sender="Lertify01",
    destinations="+38640123456",
    content="Test message",
    is_unicode=True,
)
print(response)

```

### Delivery Reports & Price Reporting

**Delivery Report URL:**

```python
response = client.send_sms(
    sender="Lertify01",
    destinations="+38640123456",
    content="Please send a delivery report.",
    delivery_report_url="[https://example.com/api/delivery-report](https://example.com/api/delivery-report)",
)
print(response)

```

*Note: The URL must be publicly accessible and return an HTTP 2xx response.*

**Enable Price Reporting:**

```python
response = client.send_sms(
    sender="Lertify01",
    destinations=[
        "+38640123456",
        "+38640987654",
    ],
    content="Price reporting is enabled.",
    price_report=True,
)
print(response)

```

*Note: Price information is not returned immediately; it may be included later in the delivery webhook.*

### Scheduling Messages

To schedule for a future time, you can directly supply a Unix timestamp or `datetime` object to the `scheduled_time` parameter of `send_sms`.

**Using a Unix timestamp (`time.time()`):**

```python
import time

scheduled_time = int(time.time()) + 3600  # 1 hour from now

response = client.send_sms(
    sender="Lertify01",
    destinations="+38640123456",
    content="This SMS is scheduled for one hour from now.",
    scheduled_time=scheduled_time,
)
print(response)

```

**Using the client timestamp helper:**

```python
scheduled_time = client.get_unix_timestamp() + (15 * 60)  # 15 minutes from now

response = client.send_sms(
    sender="Lertify01",
    destinations="+38640123456",
    content="Scheduled for 15 minutes from now.",
    scheduled_time=scheduled_time,
)
print(response)

```

**Using `datetime` objects:**

```python
from datetime import datetime, timedelta, timezone

scheduled_at = datetime.now(timezone.utc) + timedelta(hours=2)

response = client.send_sms(
    sender="Lertify01",
    destinations="+38640123456",
    content="Scheduled using a datetime object.",
    scheduled_time=scheduled_at,
)
print(response)

```

**Using a specific UTC target time:**

```python
from datetime import datetime, timezone

scheduled_at = datetime(
    2026, 10, 1, 15, 30, 0,
    tzinfo=timezone.utc,
)

response = client.send_sms(
    sender="+38640123456",
    destinations="+38640987654",
    content="Scheduled for a specific UTC time.",
    scheduled_time=scheduled_at,
)
print(response)

```

## Error Handling

```python
from lertify_sms import (
    LertifyAPIError,
    LertifyNetworkError,
    LertifySMSClient,
)

try:
    response = client.send_sms(
        sender="Lertify01",
        destinations="+38640123456",
        content="Test message",
    )
    print("Request accepted:", response)

except ValueError as exc:
    print("Input validation error:", exc)

except LertifyNetworkError as exc:
    print("Network error:", exc)

except LertifyAPIError as exc:
    print("Lertify API error:", exc)
    print("HTTP status:", exc.status_code)
    print("Response data:", exc.response_data)

```

## Complete Application Example

```python
import os
from datetime import datetime, timedelta, timezone

from lertify_sms import (
    LertifyAPIError,
    LertifyNetworkError,
    LertifySMSClient,
)


def main() -> None:
    client = LertifySMSClient(
        api_key=os.environ["LERTIFY_API_KEY"]
    )

    recipients = [
        "+38640123456",
        "+38640987654",
    ]

    scheduled_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    try:
        response = client.send_sms(
            sender="+38640123456",
            destinations=recipients,
            content="Scheduled message from the Lertify Python client.",
            scheduled_time=scheduled_at,
            price_report=True,
        )

        print("Message accepted by the API.")
        print("API status:", response.get("status"))
        print("Segment count:", response.get("segmentCount"))

        for message in response.get("messages", []):
            print("Message ID:", message.get("messageId"))
            print("Destination:", message.get("destination"))

    except ValueError as exc:
        print(f"Invalid input: {exc}")

    except LertifyNetworkError as exc:
        print(f"Network failure: {exc}")

    except LertifyAPIError as exc:
        print(f"API failure: {exc}")
        print(f"API response: {exc.response_data}")


if __name__ == "__main__":
    main()

```

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Top contributors:

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.