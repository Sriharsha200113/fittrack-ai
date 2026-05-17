import httpx
import tempfile
import os
from backend.core.config import settings

BRIDGE_URL = settings.BRIDGE_URL


async def send_message(group_id: str, message: str):
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            await client.post(f"{BRIDGE_URL}/send", json={"group_id": group_id, "message": message})
        except Exception as e:
            print(f"Send error: {e}")


async def send_pdf(group_id: str, pdf_bytes: bytes, filename: str, caption: str = ""):
    """Write PDF to temp file, send via bridge, clean up."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, prefix=filename) as f:
        f.write(pdf_bytes)
        tmp_path = f.name
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                f"{BRIDGE_URL}/send-document",
                json={"group_id": group_id, "file_path": tmp_path, "caption": caption},
            )
    except Exception as e:
        print(f"Send PDF error: {e}")
    finally:
        os.unlink(tmp_path)
