import logging
from typing import BinaryIO
import io
import asyncio
import httpx
from fastapi import HTTPException

from backend.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class SpeechService:
    """Service for handling Text-to-Speech (TTS) and Speech-to-Text (STT).
    
    Uses Deepgram for both STT (transcription) and TTS (Aura models).
    """

    @classmethod
    async def text_to_speech(cls, text: str, voice_id: str = "aura-asteria-en", personality_mode: str = "professional") -> bytes:
        """Convert conversational text to spoken audio using Deepgram TTS.
        
        Args:
            text: The text to convert to speech.
            voice_id: The default Deepgram Aura voice profile (overridden by personality_mode if set).
            personality_mode: The tone of the interviewer (friendly, strict, professional).
            
        Returns:
            The raw audio bytes (e.g., MP3 or WAV format).
        """
        if personality_mode == "friendly":
            voice_id = "aura-asteria-en" # Warm female voice
        elif personality_mode in ["strict", "faang"]:
            voice_id = "aura-orion-en" # Stern male voice
        else:
            voice_id = "aura-arcas-en" # Professional male voice

        logger.info(f"TTS requested for: '{text}' using voice: {voice_id} (mode: {personality_mode})")
        
        api_key = settings.deepgram_api_key
        if not api_key:
            logger.warning("Deepgram API key missing. Returning stub audio.")
            return b"RIFF\\x24\\x00\\x00\\x00WAVEfmt \\x10\\x00\\x00\\x00\\x01\\x00\\x01\\x00D\\xac\\x00\\x00\\x88X\\x01\\x00\\x02\\x00\\x10\\x00data\\x00\\x00\\x00\\x00"

        url = f"https://api.deepgram.com/v1/speak?model={voice_id}"
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json"
        }
        payload = {"text": text}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload, timeout=10.0)
                response.raise_for_status()
                return response.content
            except Exception as e:
                logger.error(f"Deepgram TTS error: {e}")
                raise HTTPException(status_code=500, detail="Text-to-Speech generation failed.")

    @classmethod
    async def speech_to_text(cls, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """Convert spoken audio back to text using Deepgram STT.
        
        Args:
            audio_bytes: The raw audio data.
            filename: The filename (useful for extensions).
            
        Returns:
            The transcribed text.
        """
        logger.info(f"STT requested for audio payload of size: {len(audio_bytes)} bytes")
        
        api_key = settings.deepgram_api_key
        if not api_key:
            logger.warning("Deepgram API key missing. Returning stub transcript.")
            return "This is a transcribed mock response from the candidate."

        url = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true"
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/octet-stream"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, content=audio_bytes, timeout=15.0)
                response.raise_for_status()
                data = response.json()
                transcript = data.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("transcript", "")
                return transcript
            except Exception as e:
                logger.error(f"Deepgram STT error: {e}")
                raise HTTPException(status_code=500, detail="Speech-to-Text transcription failed.")
