"""
WhatsApp Cloud API client.
Handles sending messages, images, and reading incoming messages.
"""

import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

GRAPH_API_URL = "https://graph.facebook.com/v22.0"


class WhatsAppClient:
    def __init__(self, phone_number_id: str, access_token: str):
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.base_url = f"{GRAPH_API_URL}/{phone_number_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    async def send_text(self, to: str, message: str) -> dict:
        """Send a plain text message."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        return await self._post(payload)

    async def send_template(self, to: str, template_name: str,
                             language: str = "en_US",
                             components: Optional[list] = None) -> dict:
        """Send a WhatsApp template message."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
                "components": components or []
            }
        }
        return await self._post(payload)

    async def send_interactive_buttons(self, to: str, body: str,
                                        buttons: list[dict]) -> dict:
        """Send message with quick-reply buttons."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": btn["id"],
                                "title": btn["title"][:20]  # max 20 chars
                            }
                        }
                        for btn in buttons[:3]  # max 3 buttons
                    ]
                }
            }
        }
        return await self._post(payload)

    async def send_reaction(self, to: str, message_id: str, emoji: str) -> dict:
        """React to a message with an emoji."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "reaction",
            "reaction": {
                "message_id": message_id,
                "emoji": emoji
            }
        }
        return await self._post(payload)

    async def get_media_url(self, media_id: str) -> Optional[str]:
        """Get download URL for a media object (photo)."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GRAPH_API_URL}/{media_id}",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            if resp.status_code == 200:
                return resp.json().get("url")
            logger.error(f"Failed to get media URL for {media_id}: {resp.text}")
            return None

    async def download_media(self, media_url: str) -> Optional[bytes]:
        """Download media content from WhatsApp CDN."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                media_url,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            if resp.status_code == 200:
                return resp.content
            return None

    async def _post(self, payload: dict) -> dict:
        """Make a POST request to the WhatsApp Messages API."""
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload
                )
                resp.raise_for_status()
                result = resp.json()
                logger.info(f"✅ WhatsApp message sent: {result.get('messages', [{}])[0].get('id', 'unknown')}")
                return result
            except httpx.HTTPStatusError as e:
                logger.error(f"❌ WhatsApp API error {e.response.status_code}: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"❌ WhatsApp send failed: {e}")
                raise


def extract_message_data(webhook_message: dict) -> dict:
    """
    Parse a WhatsApp webhook message into a clean dict.
    Returns: {from, message_id, type, text, image_id, timestamp, button_id}
    """
    msg_type = webhook_message.get("type", "")
    return {
        "from": webhook_message.get("from", ""),
        "message_id": webhook_message.get("id", ""),
        "type": msg_type,
        "timestamp": webhook_message.get("timestamp", ""),
        # Text content
        "text": webhook_message.get("text", {}).get("body", "") if msg_type == "text" else "",
        # Image/photo
        "image_id": webhook_message.get("image", {}).get("id", "") if msg_type == "image" else "",
        "image_caption": webhook_message.get("image", {}).get("caption", "") if msg_type == "image" else "",
        # Button replies
        "button_id": webhook_message.get("interactive", {}).get("button_reply", {}).get("id", "") if msg_type == "interactive" else "",
        "button_title": webhook_message.get("interactive", {}).get("button_reply", {}).get("title", "") if msg_type == "interactive" else "",
    }
