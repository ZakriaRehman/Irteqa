"use client"

import { useEffect, useState, useRef } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Mic, MicOff, CheckCircle, FileText, Activity } from "lucide-react"
import { AudioRecorder } from "@/lib/audio/recorder"
import { toast } from "sonner"
import { useSession, useStartSession, useCompleteSession } from "@/lib/hooks/use-sessions"

interface TranscriptSegment {
  text: string
  is_final: boolean
  speaker?: number
  timestamp: number
}

interface SavedTranscriptSegment {
  index: number
  text: string
  timestamp: string | null
}

export default function LiveSessionPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string

  const { data: sessionData } = useSession(sessionId)
  const startSession = useStartSession()
  const completeSession = useCompleteSession()

  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState<TranscriptSegment[]>([])
  const [currentInterim, setCurrentInterim] = useState("")
  const [wsConnected, setWsConnected] = useState(false)
  const [viewMode, setViewMode] = useState<"live" | "saved">("live")
  const [savedTranscript, setSavedTranscript] = useState<SavedTranscriptSegment[]>([])
  const [loadingSaved, setLoadingSaved] = useState(false)

  const recorderRef = useRef<AudioRecorder | null>(null)
  const transcriptEndRef = useRef<HTMLDivElement>(null)

  // Fetch saved transcript when switching to saved view
  useEffect(() => {
    if (viewMode === "saved" && savedTranscript.length === 0) {
      fetchSavedTranscript()
    }
  }, [viewMode])

  // Auto-scroll to latest transcript
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [transcript, currentInterim])

  const fetchSavedTranscript = async () => {
    setLoadingSaved(true)
    try {
      const response = await fetch(`http://localhost:8000/v1/sessions/${sessionId}/transcript`, {
        headers: {
          "X-Tenant-ID": "tenant_001",
        },
      })

      if (!response.ok) throw new Error("Failed to fetch transcript")

      const data = await response.json()
      setSavedTranscript(data.segments || [])

      if (!data.has_transcript) {
        toast.info("No saved transcript available yet")
      }
    } catch (error) {
      console.error("Error fetching saved transcript:", error)
      toast.error("Failed to load saved transcript")
    } finally {
      setLoadingSaved(false)
    }
  }

  const handleStartSession = async () => {
    try {
      // Request microphone permission
      const recorder = new AudioRecorder((error) => {
        toast.error(`Microphone error: ${error.message}`)
      })

      const hasPermission = await recorder.requestPermission()
      if (!hasPermission) {
        toast.error("Microphone access is required for live sessions")
        return
      }

      // Start session on backend
      const data = await startSession.mutateAsync(sessionId)

      if (!data.rt?.ws_audio_url) {
        throw new Error("No WebSocket URL provided")
      }

      // Start recording and streaming
      await recorder.start(data.rt.ws_audio_url)
      recorderRef.current = recorder

      // Listen for transcript messages
      const ws = recorder.getWebSocket()
      if (ws) {
        ws.onmessage = (event) => {
          const message = JSON.parse(event.data)

          if (message.type === "transcript") {
            if (message.is_final) {
              // Add to permanent transcript
              setTranscript((prev) => [
                ...prev,
                {
                  text: message.text,
                  is_final: true,
                  speaker: message.speaker,
                  timestamp: Date.now(),
                },
              ])
              setCurrentInterim("")
            } else {
              // Update interim transcript
              setCurrentInterim(message.text)
            }
          }
        }

        ws.onopen = () => {
          setWsConnected(true)
          toast.success("Connected to live transcription")
        }

        ws.onclose = () => {
          setWsConnected(false)
          toast.info("Disconnected from transcription")
        }
      }

      setIsRecording(true)
      toast.success("Session started")
    } catch (error) {
      console.error("Error starting session:", error)
      toast.error("Failed to start session")
    }
  }

  const handleStopSession = () => {
    if (recorderRef.current) {
      recorderRef.current.stop()
      recorderRef.current = null
    }
    setIsRecording(false)
    setWsConnected(false)
    toast.success("Recording stopped")
  }

  const handleCompleteSession = async () => {
    try {
      handleStopSession()

      await completeSession.mutateAsync(sessionId)

      toast.success("Session completed! Redirecting...")
      router.push("/sessions")
    } catch (error) {
      console.error("Error completing session:", error)
      toast.error("Failed to complete session")
    }
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Panel - Transcript */}
      <div className="flex-1 flex flex-col p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold">Session Transcript</h1>
            {sessionData?.client_name && (
              <p className="text-gray-600">Client: {sessionData.client_name}</p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {wsConnected && viewMode === "live" && (
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                <span className="h-2 w-2 bg-green-500 rounded-full mr-2 animate-pulse" />
                Live
              </Badge>
            )}
          </div>
        </div>

        {/* View Mode Tabs */}
        <div className="flex gap-2 mb-4">
          <Button
            variant={viewMode === "live" ? "default" : "outline"}
            onClick={() => setViewMode("live")}
            className="flex-1"
          >
            <Activity className="mr-2 h-4 w-4" />
            Live Session
          </Button>
          <Button
            variant={viewMode === "saved" ? "default" : "outline"}
            onClick={() => setViewMode("saved")}
            className="flex-1"
          >
            <FileText className="mr-2 h-4 w-4" />
            Saved Transcript
          </Button>
        </div>

        {/* Transcript Display */}
        <Card className="flex-1 p-6 overflow-y-auto bg-white">
          {viewMode === "live" ? (
            // Live Transcript View
            <>
              {transcript.length === 0 && !currentInterim && (
                <div className="flex items-center justify-center h-full text-gray-400">
                  <p>Transcript will appear here once session starts...</p>
                </div>
              )}

              <div className="space-y-4">
                {transcript.map((segment, index) => (
                  <div key={index} className="flex gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-xs font-medium text-blue-700">
                      {segment.speaker !== undefined ? `S${segment.speaker}` : "?"}
                    </div>
                    <div className="flex-1">
                      <p className="text-gray-900">{segment.text}</p>
                      <span className="text-xs text-gray-400">
                        {new Date(segment.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                ))}

                {currentInterim && (
                  <div className="flex gap-3 opacity-60">
                    <div className="flex-shrink-0 w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-xs font-medium text-gray-500">
                      ?
                    </div>
                    <div className="flex-1">
                      <p className="text-gray-600 italic">{currentInterim}</p>
                    </div>
                  </div>
                )}

                <div ref={transcriptEndRef} />
              </div>
            </>
          ) : (
            // Saved Transcript View
            <>
              {loadingSaved ? (
                <div className="flex items-center justify-center h-full text-gray-400">
                  <p>Loading saved transcript...</p>
                </div>
              ) : savedTranscript.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-400">
                  <FileText className="h-12 w-12 mb-4" />
                  <p className="text-lg font-medium">No saved transcript yet</p>
                  <p className="text-sm mt-2">Start a live session to generate a transcript</p>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center justify-between mb-4 pb-4 border-b">
                    <div>
                      <h3 className="font-semibold text-lg">Saved Transcript</h3>
                      <p className="text-sm text-gray-600">{savedTranscript.length} segments</p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={fetchSavedTranscript}
                    >
                      Refresh
                    </Button>
                  </div>

                  {savedTranscript.map((segment) => (
                    <div key={segment.index} className="border-l-2 border-blue-200 pl-4 py-2">
                      <div className="flex items-start gap-2">
                        <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded">
                          #{segment.index}
                        </span>
                        <p className="flex-1 text-gray-900">{segment.text}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </Card>

        {/* Controls - Only show in live mode */}
        {viewMode === "live" && (
          <div className="flex items-center justify-center gap-4 mt-6">
            {!isRecording ? (
              <Button
                onClick={handleStartSession}
                size="lg"
                className="bg-blue-600 hover:bg-blue-700"
                disabled={startSession.isPending}
              >
                <Mic className="mr-2 h-5 w-5" />
                Start Session
              </Button>
            ) : (
              <>
                <Button
                  onClick={handleStopSession}
                  size="lg"
                  variant="outline"
                  className="border-red-300 text-red-600 hover:bg-red-50"
                >
                  <MicOff className="mr-2 h-5 w-5" />
                  Stop Recording
                </Button>
                <Button
                  onClick={handleCompleteSession}
                  size="lg"
                  className="bg-green-600 hover:bg-green-700"
                  disabled={completeSession.isPending}
                >
                  <CheckCircle className="mr-2 h-5 w-5" />
                  Complete Session
                </Button>
              </>
            )}
          </div>
        )}
      </div>

      {/* Right Panel - Session Info */}
      <div className="w-96 bg-white border-l p-6">
        <h2 className="text-lg font-semibold mb-4">Session Info</h2>
        <Card className="p-4 bg-blue-50 border-blue-200 mb-6">
          <p className="text-sm text-blue-800">
            💡 {viewMode === "live"
              ? (isRecording ? "Session in progress" : "Ready to start session")
              : "Viewing saved transcript"}
          </p>
        </Card>

        <div className="space-y-4">
          {viewMode === "live" ? (
            <>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Duration</h3>
                <p className="text-lg font-semibold">
                  {isRecording ? "Recording..." : "Not started"}
                </p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Live Segments</h3>
                <p className="text-lg font-semibold">{transcript.length} segments</p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Status</h3>
                <Badge className={wsConnected ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}>
                  {wsConnected ? "Connected" : "Disconnected"}
                </Badge>
              </div>
            </>
          ) : (
            <>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Saved Segments</h3>
                <p className="text-lg font-semibold">{savedTranscript.length} segments</p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Session Status</h3>
                <Badge className="bg-gray-100 text-gray-800">
                  {sessionData?.status || "Unknown"}
                </Badge>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Actions</h3>
                <div className="space-y-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={fetchSavedTranscript}
                  >
                    Refresh Transcript
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
