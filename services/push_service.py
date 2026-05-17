import time
import json
import httpx
import PyJWT
from backend.core.config import settings

APNS_HOST_SANDBOX = "https://api.sandbox.push.apple.com"
APNS_HOST_PROD = "https://api.push.apple.com"


def _make_apns_jwt() -> str:
    now = int(time.time())
    return PyJWT.encode(
        {"iss": settings.APNS_TEAM_ID, "iat": now},
        settings.APNS_PRIVATE_KEY,
        algorithm="ES256",
        headers={"kid": settings.APNS_KEY_ID},
    )


async def send_push(device_token: str, title: str, body: str, data: dict | None = None) -> bool:
    if not settings.APNS_KEY_ID or not settings.APNS_TEAM_ID or not settings.APNS_PRIVATE_KEY:
        return False

    host = APNS_HOST_SANDBOX if settings.APNS_SANDBOX else APNS_HOST_PROD
    url = f"{host}/3/device/{device_token}"

    payload = {
        "aps": {
            "alert": {"title": title, "body": body},
            "sound": "default",
        }
    }
    if data:
        payload.update(data)

    headers = {
        "authorization": f"bearer {_make_apns_jwt()}",
        "apns-topic": settings.APNS_BUNDLE_ID,
        "apns-push-type": "alert",
    }

    async with httpx.AsyncClient(http2=True) as client:
        resp = await client.post(url, json=payload, headers=headers)
        return resp.status_code == 200
