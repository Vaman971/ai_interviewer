"""Media API routes: STT, TTS, and Avatar streaming endpoints.

Provides WebSockets and standard HTTP endpoints for Voice/Video interactions.
"""

from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from backend.app.services.speech_service import SpeechService
from backend.app.services.avatar_service import AvatarService
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/media", tags=["media"])


@router.websocket("/stream")
async def websocket_media_stream(websocket: WebSocket):
    """Bidirectional WebSocket for real-time STT and Interviewer responses.
    
    Accepts audio chunks from the client, transcribes them, and eventually
    can return the AI's spoken response (TTS audio) directly through the socket.
    """
    await websocket.accept()
    logger.info("Client connected to media stream WebSocket")
    
    try:
        while True:
            # Client sends a JSON message describing the payload or raw bytes
            data = await websocket.receive_bytes()
            
            # Step 1: STT
            transcript = await SpeechService.speech_to_text(data)
            
            # Echo back what we heard as an event
            await websocket.send_json({
                "type": "transcript",
                "text": transcript
            })
            
            # In a full flow, the transcript goes to the agents, then to TTS
            # and finally the audio is streamed back to the client.

    except WebSocketDisconnect:
        logger.info("Client disconnected from media stream WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try: 
            await websocket.close()
        except:
            pass


@router.post("/tts")
async def text_to_speech(text: str):
    """Convert text to speech audio. (Useful for fallback HTTP pooling)"""
    audio_bytes = await SpeechService.text_to_speech(text)
    return Response(content=audio_bytes, media_type="audio/mpeg")


@router.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    """Convert uploaded audio file to text."""
    content = await file.read()
    transcript = await SpeechService.speech_to_text(content, filename=file.filename)
    return {"transcript": transcript}


from pydantic import BaseModel

class AvatarSessionRequest(BaseModel):
    personality_mode: str = "professional"

class AvatarSpeakRequest(BaseModel):
    conversation_id: str
    text: str

@router.post("/avatar/session")
async def create_avatar_session(request: AvatarSessionRequest):
    """
    Initialize a Tavus conversational video WebRTC session.
    Returns {conversation_id, conversation_url}.
    """
    response = await AvatarService.create_conversation(request.personality_mode)
    return response

@router.post("/avatar/speak")
async def avatar_speak(request: AvatarSpeakRequest):
    """
    Send text directly to an active Tavus conversation for the avatar to speak.
    """
    response = await AvatarService.send_message(request.conversation_id, request.text)
    return response
