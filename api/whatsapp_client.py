"""
WhatsApp Cloud API Client
Handles sending messages via WhatsApp Business API
"""

import os
import httpx
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class WhatsAppClient:
    """Client for WhatsApp Cloud API"""
    
    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.api_version = "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}"
        
        if not self.access_token:
            raise ValueError("WHATSAPP_ACCESS_TOKEN not found in environment variables")
        if not self.phone_number_id:
            raise ValueError("WHATSAPP_PHONE_NUMBER_ID not found in environment variables")
    
    async def send_text_message(self, to: str, message: str) -> Dict[str, Any]:
        """
        Send a text message to a WhatsApp user
        
        Args:
            to: Phone number in international format (e.g., "1234567890")
            message: Text message to send
            
        Returns:
            API response dict
        """
        url = f"{self.base_url}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": True,  # Enable link previews
                "body": message
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    async def send_template_message(self, to: str, template_name: str, language_code: str = "en") -> Dict[str, Any]:
        """
        Send a template message (for notifications outside 24h window)
        
        Args:
            to: Phone number
            template_name: Name of approved template
            language_code: Language code (default: en)
        """
        url = f"{self.base_url}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    async def send_reaction(self, to: str, message_id: str, emoji: str) -> Dict[str, Any]:
        """
        React to a message with an emoji
        
        Args:
            to: Phone number
            message_id: ID of message to react to
            emoji: Emoji to react with (e.g., "👍", "❤️")
        """
        url = f"{self.base_url}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
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
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    async def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """
        Mark a message as read
        
        Args:
            message_id: ID of message to mark as read
        """
        url = f"{self.base_url}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    async def send_interactive_buttons(
        self, 
        to: str, 
        body_text: str, 
        buttons: list[Dict[str, str]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an interactive message with buttons
        
        Args:
            to: Phone number
            body_text: Main message text
            buttons: List of button dicts with 'id' and 'title' keys (max 3)
            header_text: Optional header text
            footer_text: Optional footer text
        """
        if len(buttons) > 3:
            raise ValueError("Maximum 3 buttons allowed")
        
        url = f"{self.base_url}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        action_buttons = [
            {
                "type": "reply",
                "reply": {
                    "id": btn["id"],
                    "title": btn["title"][:20]  # Max 20 chars
                }
            }
            for btn in buttons
        ]
        
        interactive_payload = {
            "type": "button",
            "body": {"text": body_text},
            "action": {"buttons": action_buttons}
        }
        
        if header_text:
            interactive_payload["header"] = {"type": "text", "text": header_text}
        if footer_text:
            interactive_payload["footer"] = {"text": footer_text}
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive_payload
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
