"use client"

import { useSessions, useCreateSession } from "@/lib/hooks/use-sessions"
import { useCreatePatient } from "@/lib/hooks/use-patients"
import { SessionCard } from "@/components/sessions/session-card"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Plus } from "lucide-react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"

export default function SessionsPage() {
  const router = useRouter()
  const { data: sessions = [], isLoading } = useSessions()
  const createSession = useCreateSession()
  const createPatient = useCreatePatient()

  const handleQuickStart = async () => {
    try {
      toast.info("Creating session...")

      // Create patient first
      const patient = await createPatient.mutateAsync({
        name: `Test Client ${Date.now()}`,
        email: `test-${Date.now()}@example.com`,
        status: "active",
      })

      // Create session
      const session = await createSession.mutateAsync({
        client_id: patient.id,
        therapist_id: "therapist_001",
        start_at: new Date().toISOString(),
        status: "scheduled",
      })

      // Redirect to live session
      router.push(`/sessions/${session.id}/live`)
    } catch (error) {
      console.error("Error creating session:", error)
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-gray-500">Loading sessions...</p>
      </div>
    )
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Therapy Sessions</h1>
          <p className="text-gray-600 mt-1">Manage and start live sessions</p>
        </div>
        <Button
          onClick={handleQuickStart}
          size="lg"
          disabled={createSession.isPending || createPatient.isPending}
        >
          <Plus className="mr-2 h-5 w-5" />
          Quick Start Session
        </Button>
      </div>

      {/* Sessions List */}
      {sessions.length === 0 ? (
        <Card className="p-12 text-center">
          <p className="text-gray-500 mb-4">No sessions yet</p>
          <Button onClick={handleQuickStart}>
            <Plus className="mr-2 h-4 w-4" />
            Create Your First Session
          </Button>
        </Card>
      ) : (
        <div className="space-y-4">
          {sessions.map((session) => (
            <SessionCard key={session.id} session={session} />
          ))}
        </div>
      )}
    </div>
  )
}
