"""
WebSocket handler for live therapy sessions
Manages real-time audio streaming and transcript broadcasting
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.deepgram_service import deepgram_service
from app.models import Session


class ConnectionManager:
    """Manages WebSocket connections for sessions"""
    
    def __init__(self):
        # session_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # session_id -> transcript buffer
        self.transcript_buffers: Dict[str, list] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
            self.transcript_buffers[session_id] = []
        
        self.active_connections[session_id].add(websocket)
        print(f"[WS] Client connected to session {session_id}")
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection"""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            
            # Clean up if no more connections
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
                if session_id in self.transcript_buffers:
                    del self.transcript_buffers[session_id]
        
        print(f"[WS] Client disconnected from session {session_id}")
    
    async def broadcast(self, session_id: str, message: dict):
        """Broadcast message to all connected clients for a session"""
        if session_id in self.active_connections:
            disconnected = set()
            
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            # Remove disconnected clients
            for connection in disconnected:
                self.disconnect(connection, session_id)
    
    def add_to_transcript(self, session_id: str, text: str, is_final: bool):
        """Add text to transcript buffer"""
        if session_id not in self.transcript_buffers:
            self.transcript_buffers[session_id] = []
        
        self.transcript_buffers[session_id].append({
            "text": text,
            "is_final": is_final,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    def get_transcript(self, session_id: str) -> list:
        """Get full transcript for a session"""
        return self.transcript_buffers.get(session_id, [])


# Global manager instance
manager = ConnectionManager()


async def handle_audio_websocket(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession
):
    """
    Handle audio WebSocket connection
    Receives audio from client and sends to Deepgram
    """
    await manager.connect(websocket, session_id)
    
    # Verify session exists
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        await websocket.send_json({"error": "Session not found"})
        await websocket.close()
        return
    
    # Callback for Deepgram transcripts
    async def on_transcript(data):
        """Handle transcript from Deepgram"""
        try:
            # Store in buffer
            manager.add_to_transcript(
                session_id,
                data["text"],
                data["is_final"]
            )
            
            # Broadcast to all connected clients
            await manager.broadcast(session_id, {
                "type": "transcript",
                "text": data["text"],
                "is_final": data["is_final"],
                "speaker": data.get("speaker"),
                "session_id": session_id
            })
            
            # Store final transcripts in database
            if data["is_final"]:
                # Append to session transcript
                existing = session.transcript or ""
                session.transcript = existing + "\n" + data["text"]
                await db.commit()
                
        except Exception as e:
            print(f"Error handling transcript: {e}")
    
    # Start Deepgram connection
    try:
        if deepgram_service:
            await deepgram_service.create_live_transcription(
                session_id=session_id,
                on_transcript=on_transcript
            )
        else:
            await websocket.send_json({"error": "Deepgram service not available"})
            await websocket.close()
            return
        
        # Listen for audio data from client
        try:
            while True:
                # Receive audio data
                data = await websocket.receive()
                
                if "bytes" in data:
                    # Audio data - send to Deepgram
                    audio_data = data["bytes"]
                    await deepgram_service.send_audio(session_id, audio_data)
                
                elif "text" in data:
                    # Control messages
                    message = json.loads(data["text"])
                    
                    if message.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    
                    elif message.get("type") == "stop":
                        break
        
        except WebSocketDisconnect:
            print(f"WebSocket disconnected for session {session_id}")
        
        finally:
            # Clean up
            manager.disconnect(websocket, session_id)
            if deepgram_service:
                await deepgram_service.close_connection(session_id)
    
    except Exception as e:
        print(f"Error in audio WebSocket: {e}")
        await websocket.send_json({"error": str(e)})
        await websocket.close()


async def handle_transcript_stream(
    websocket: WebSocket,
    session_id: str
):
    """
    Handle transcript-only WebSocket connection
    Broadcasts transcripts without receiving audio
    """
    await manager.connect(websocket, session_id)
    
    try:
        # Send initial transcript history
        transcript = manager.get_transcript(session_id)
        await websocket.send_json({
            "type": "history",
            "transcript": transcript
        })
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
            except WebSocketDisconnect:
                break
    
    finally:
        manager.disconnect(websocket, session_id)