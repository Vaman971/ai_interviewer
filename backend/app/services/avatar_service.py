import logging
import asyncio
import httpx
from fastapi import HTTPException

from backend.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

TAVUS_API_URL = "https://tavusapi.com/v2/conversations"

class AvatarService:
    @staticmethod
    def _get_replica_for_personality(personality_mode: str) -> str:
        """Map personality mode to a specific Tavus Replica ID."""
        # A valid stock Tavus replica ID is 'rfb0463909e3' (James - Office).
        # We use this for all personalities in this generic integration test.
        replica_map = {
            "professional": "rfb0463909e3",
            "friendly": "rfb0463909e3",
            "strict": "rfb0463909e3",
        }
        return replica_map.get(personality_mode, "rfb0463909e3") # Default to professional if mode not found

    @classmethod
    async def create_conversation(cls, personality_mode: str = "professional") -> dict:
        """
        Create a new Tavus WebRTC conversation.
        Returns the conversation_id, conversation_url (WebRTC endpoint).
        """
        api_key = settings.tavus_api_key
        if not api_key:
            raise HTTPException(status_code=500, detail="TAVUS_API_KEY is not configured.")

        replica_id = cls._get_replica_for_personality(personality_mode)
        
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "replica_id": replica_id,
        }

        logger.info(f"Creating Tavus conversation with replica: {replica_id}")
        
        async with httpx.AsyncClient() as client:
            try:
                # Need to use post with the properties
                response = await client.post(TAVUS_API_URL, json=payload, headers=headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                return {
                    "conversation_id": data.get("conversation_id"),
                    "conversation_url": data.get("conversation_url"),
                    "status": "success"
                }
            except httpx.HTTPStatusError as e:
                logger.error(f"Tavus API error creating conversation: {e.response.text}")
                error_detail = "Failed to initialize Avatar conversation."
                try:
                    err_json = e.response.json()
                    if "message" in err_json:
                        error_detail = f"Tavus API Error: {err_json['message']}"
                except Exception:
                    pass
                raise HTTPException(status_code=e.response.status_code, detail=error_detail)
            except Exception as e:
                logger.error(f"Tavus API connection error: {e}")
                raise HTTPException(status_code=500, detail="Could not reach Tavus API.")

    @classmethod
    async def send_message(cls, conversation_id: str, text: str) -> dict:
        """
        Make the active Tavus avatar speak the text asynchronously.
        """
        api_key = settings.tavus_api_key
        if not api_key:
            raise HTTPException(status_code=500, detail="TAVUS_API_KEY is not configured.")

        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        endpoint = f"{TAVUS_API_URL}/{conversation_id}/messages"
        payload = {
            "text": text
        }
        
        logger.info(f"Sending message to Tavus conversation {conversation_id}: {text[:50]}...")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(endpoint, json=payload, headers=headers, timeout=5.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Tavus message error: {e.response.text}")
                return {"status": "error", "message": str(e)}
            except Exception as e:
                logger.error(f"Tavus message connection error: {e}")
                return {"status": "error", "message": str(e)}
