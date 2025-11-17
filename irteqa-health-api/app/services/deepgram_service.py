""""
Deepgram Integration Service
Handles real-time audio transcription using Deepgram API
"""

import os
from dotenv import load_dotenv  # ADD THIS
import json
from typing import AsyncIterator, Optional
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from deepgram.clients.live.v1 import LiveClient

# Load environment variables from .env file
load_dotenv()  # ADD THIS LINE

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

if not DEEPGRAM_API_KEY:
    print("[WARNING] DEEPGRAM_API_KEY not set. Live transcription will not work.")


class DeepgramService:
    """Service for managing Deepgram live transcription"""
    
    def __init__(self):
        if not DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY environment variable is required")
        
        self.client = DeepgramClient(DEEPGRAM_API_KEY)
        self.active_connections = {}
    
    async def create_live_transcription(
        self,
        session_id: str,
        on_transcript: callable,
        on_error: callable = None,
        language: str = "en-US"
    ) -> LiveClient:
        """
        Create a live transcription connection

        Args:
            session_id: Unique session identifier
            on_transcript: Callback for transcript results
            on_error: Callback for errors
            language: Language code (default: en-US)

        Returns:
            LiveClient connection
        """

        import asyncio

        # Get the current event loop to use in callbacks
        loop = asyncio.get_event_loop()

        # Configure transcription options
        options = LiveOptions(
            model="nova-2",
            language=language,
            smart_format=True,
            interim_results=True,
            punctuate=True,
            diarize=True,  # Speaker diarization
            utterance_end_ms=1000,
            vad_events=True,
        )

        # Create connection
        connection = self.client.listen.live.v("1")

        # Set up event handlers
        def on_message(dg_self, result, **kwargs):
            """Handle incoming transcript"""
            try:
                sentence = result.channel.alternatives[0].transcript

                if sentence:
                    # Extract metadata
                    is_final = result.is_final
                    speech_final = result.speech_final

                    # Get speaker info if available
                    speaker = None
                    if result.channel.alternatives[0].words:
                        speaker = result.channel.alternatives[0].words[0].speaker

                    print(f"[TRANSCRIPT] '{sentence}' (final: {is_final}, speaker: {speaker})")

                    # Schedule the callback in the event loop
                    asyncio.run_coroutine_threadsafe(
                        on_transcript({
                            "text": sentence,
                            "is_final": is_final,
                            "speech_final": speech_final,
                            "speaker": speaker,
                            "session_id": session_id
                        }),
                        loop
                    )
            except Exception as e:
                print(f"Error processing transcript: {e}")
                import traceback
                traceback.print_exc()
                if on_error:
                    on_error(e)

        def on_error_event(dg_self, error, **kwargs):
            """Handle errors"""
            print(f"[ERROR] Deepgram error: {error}")
            if on_error:
                on_error(error)

        def on_close(dg_self, close, **kwargs):
            """Handle connection close"""
            print(f"[CLOSE] Connection closed for session {session_id}")
            if session_id in self.active_connections:
                del self.active_connections[session_id]
        
        # Register event handlers
        connection.on(LiveTranscriptionEvents.Transcript, on_message)
        connection.on(LiveTranscriptionEvents.Error, on_error_event)
        connection.on(LiveTranscriptionEvents.Close, on_close)
        
        # Start connection
        if connection.start(options):
            self.active_connections[session_id] = connection
            print(f"[DEEPGRAM] Connection started for session {session_id}")
            return connection
        else:
            raise Exception("Failed to start Deepgram connection")
    
    async def send_audio(self, session_id: str, audio_data: bytes):
        """Send audio data to Deepgram for transcription"""
        connection = self.active_connections.get(session_id)
        if connection:
            connection.send(audio_data)
        else:
            raise ValueError(f"No active connection for session {session_id}")
    
    async def close_connection(self, session_id: str):
        """Close the transcription connection"""
        connection = self.active_connections.get(session_id)
        if connection:
            connection.finish()
            if session_id in self.active_connections:
                del self.active_connections[session_id]
            print(f"[DEEPGRAM] Closed connection for session {session_id}")
    
    def get_active_sessions(self):
        """Get list of active session IDs"""
        return list(self.active_connections.keys())


# Singleton instance
deepgram_service = DeepgramService() if DEEPGRAM_API_KEY else None


# Test function
async def test_deepgram():
    """Test Deepgram connection"""
    if not DEEPGRAM_API_KEY:
        print("[ERROR] DEEPGRAM_API_KEY not set")
        return

    print("[TEST] Testing Deepgram connection...")

    def on_transcript(data):
        print(f"[TRANSCRIPT] {data['text']} (final: {data['is_final']})")

    def on_error(error):
        print(f"[ERROR] {error}")

    try:
        service = DeepgramService()
        connection = await service.create_live_transcription(
            session_id="test_session",
            on_transcript=on_transcript,
            on_error=on_error
        )
        print("[SUCCESS] Connection successful!")

        # Simulate sending audio (in real scenario, this would be actual audio bytes)
        # connection.send(audio_bytes)

        # Close after test
        await service.close_connection("test_session")
        print("[SUCCESS] Test completed")

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_deepgram())